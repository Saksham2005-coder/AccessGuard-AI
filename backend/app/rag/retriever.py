"""Dense, lexical, and hybrid Reciprocal Rank Fusion (RRF) retriever for WCAG knowledge."""

import re
import uuid
from typing import Any

from rank_bm25 import BM25Okapi
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import get_logger
from app.db.models.knowledge import KnowledgeChunk
from app.rag.embeddings import EmbeddingService, get_embedding_service
from app.rag.vector_store import QdrantVectorStore, get_vector_store
from app.schemas.rag import EvidenceItem

logger = get_logger("rag_retriever")

DEFAULT_RRF_K = 60
DEFAULT_CANDIDATE_POOL = 20
DEFAULT_FINAL_LIMIT = 5
ABSTENTION_COSINE_THRESHOLD = 0.20


def tokenize_for_bm25(text: str) -> list[str]:
    """Tokenize text preserving criterion IDs (e.g. 1.4.3), ARIA attributes, and rule identifiers."""
    normalized = text.lower().strip()
    # Match dotted numbers, hyphenated tokens, or alpha-numeric words
    tokens = re.findall(r"\b\d+\.\d+(?:\.\d+)?\b|[a-z0-9]+(?:-[a-z0-9]+)*", normalized)
    return tokens if tokens else normalized.split()


class HybridRetriever:
    """Orchestrates dense vector search, lexical keyword search, and reciprocal rank fusion."""

    def __init__(
        self,
        vector_store: QdrantVectorStore | None = None,
        embedding_service: EmbeddingService | None = None,
        rrf_k: int = DEFAULT_RRF_K,
        candidate_pool_size: int = DEFAULT_CANDIDATE_POOL,
    ) -> None:
        self.vector_store = vector_store or get_vector_store()
        self.embedding_service = embedding_service or get_embedding_service()
        self.rrf_k = rrf_k
        self.candidate_pool_size = candidate_pool_size

    async def retrieve_dense(
        self,
        query: str,
        limit: int = DEFAULT_CANDIDATE_POOL,
        filter_dict: dict[str, Any] | None = None,
    ) -> list[tuple[uuid.UUID, float, dict[str, Any]]]:
        """Query Qdrant dense vector index using query embedding."""
        query_vector = self.embedding_service.embed_query(query)
        scored_points = self.vector_store.search(
            query_vector=query_vector,
            limit=limit,
            filter_dict=filter_dict,
        )
        return [(p.chunk_id, p.score, p.payload) for p in scored_points]

    async def retrieve_lexical(
        self,
        db: AsyncSession,
        query: str,
        limit: int = DEFAULT_CANDIDATE_POOL,
        criterion_id_filter: str | None = None,
    ) -> list[tuple[KnowledgeChunk, float]]:
        """Retrieve lexical candidates from PostgreSQL using BM25 and exact identifier boosts."""
        stmt = select(KnowledgeChunk).options(selectinload(KnowledgeChunk.source))
        if criterion_id_filter:
            stmt = stmt.where(KnowledgeChunk.criterion_id == criterion_id_filter)

        res = await db.execute(stmt)
        all_chunks = res.scalars().all()
        if not all_chunks:
            return []

        # Tokenize corpus for BM25
        corpus_tokens = [
            tokenize_for_bm25(f"{c.section_title or ''} {c.content}") for c in all_chunks
        ]
        query_tokens = tokenize_for_bm25(query)
        if not query_tokens:
            return []

        bm25 = BM25Okapi(corpus_tokens)
        doc_scores = bm25.get_scores(query_tokens)

        # Apply exact criterion ID boost and term overlap safeguard
        scored_chunks: list[tuple[KnowledgeChunk, float]] = []
        clean_query = query.strip().lower()
        query_token_set = set(query_tokens)

        for chunk, score in zip(all_chunks, doc_scores, strict=False):
            chunk_text = f"{chunk.section_title or ''} {chunk.content}".lower()
            matched_tokens = sum(1 for qt in query_token_set if qt in chunk_text)

            # Avoid negative BM25 IDF penalties on matching documents (e.g. single-doc corpora or high-df terms)
            base_score = max(float(score), 0.0)
            if matched_tokens > 0:
                base_score += float(matched_tokens)

            final_score = base_score
            if chunk.criterion_id and chunk.criterion_id.lower() in clean_query:
                final_score += 10.0
            if chunk.section_title:
                st_lower = chunk.section_title.lower()
                if clean_query in st_lower or st_lower in clean_query:
                    final_score += 5.0
                elif any(qt in st_lower for qt in query_tokens):
                    final_score += 2.0

            if final_score > 0.0:
                scored_chunks.append((chunk, final_score))

        # Sort descending by lexical score
        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        return scored_chunks[:limit]

    async def search(
        self,
        db: AsyncSession,
        query: str,
        criterion_id: str | None = None,
        limit: int = DEFAULT_FINAL_LIMIT,
        mode: str = "hybrid",
    ) -> tuple[list[EvidenceItem], int, bool]:
        """Perform hybrid, dense, or lexical retrieval with RRF fusion.

        Returns: (evidence_items, total_candidates, should_abstain)
        """
        clean_query = query.strip()
        if not clean_query:
            return [], 0, True

        filter_dict = {"criterion_id": criterion_id} if criterion_id else None

        # 1. Dense retrieval
        dense_results: list[tuple[uuid.UUID, float, dict[str, Any]]] = []
        if mode in ("hybrid", "dense"):
            try:
                dense_results = await self.retrieve_dense(
                    clean_query,
                    limit=self.candidate_pool_size,
                    filter_dict=filter_dict,
                )
            except Exception as e:
                logger.warning("Dense retrieval failed; continuing with lexical", error=str(e))

        # 2. Lexical retrieval
        lexical_results: list[tuple[KnowledgeChunk, float]] = []
        if mode in ("hybrid", "lexical"):
            try:
                lexical_results = await self.retrieve_lexical(
                    db=db,
                    query=clean_query,
                    limit=self.candidate_pool_size,
                    criterion_id_filter=criterion_id,
                )
            except Exception as e:
                logger.warning("Lexical retrieval failed; continuing with dense", error=str(e))

        # Abstention check when zero candidates found
        if not dense_results and not lexical_results:
            return [], 0, True

        # Check cosine similarity threshold for dense-only queries
        if mode == "dense" and dense_results and dense_results[0][1] < ABSTENTION_COSINE_THRESHOLD:
            return [], len(dense_results), True

        # 3. Reciprocal Rank Fusion (RRF)
        # Map: chunk_id -> dict of ranks and scores
        candidate_fusion: dict[uuid.UUID, dict[str, Any]] = {}

        # Process dense ranks
        for rank_idx, (c_id, score, payload) in enumerate(dense_results, start=1):
            if c_id not in candidate_fusion:
                candidate_fusion[c_id] = {
                    "dense_rank": rank_idx,
                    "dense_score": score,
                    "lexical_rank": None,
                    "payload": payload,
                    "rrf_score": 0.0,
                }
            else:
                candidate_fusion[c_id]["dense_rank"] = rank_idx
                candidate_fusion[c_id]["dense_score"] = score
            candidate_fusion[c_id]["rrf_score"] += 1.0 / (self.rrf_k + rank_idx)

        # Process lexical ranks
        for rank_idx, (chunk, score) in enumerate(lexical_results, start=1):
            c_id = chunk.id
            if c_id not in candidate_fusion:
                candidate_fusion[c_id] = {
                    "dense_rank": None,
                    "dense_score": 0.0,
                    "lexical_rank": rank_idx,
                    "lexical_score": score,
                    "chunk": chunk,
                    "rrf_score": 0.0,
                }
            else:
                candidate_fusion[c_id]["lexical_rank"] = rank_idx
                candidate_fusion[c_id]["lexical_score"] = score
                candidate_fusion[c_id]["chunk"] = chunk
            candidate_fusion[c_id]["rrf_score"] += 1.0 / (self.rrf_k + rank_idx)

        # If mode is dense only or lexical only, sort by respective score
        if mode == "dense":
            sorted_candidates = sorted(
                candidate_fusion.items(),
                key=lambda item: item[1]["dense_score"],
                reverse=True,
            )
        elif mode == "lexical":
            sorted_candidates = sorted(
                candidate_fusion.items(),
                key=lambda item: item[1].get("lexical_score", 0.0),
                reverse=True,
            )
        else:
            # Hybrid RRF: Sort by rrf_score desc, dense_score desc, str(chunk_id) asc for stability
            sorted_candidates = sorted(
                candidate_fusion.items(),
                key=lambda item: (
                    item[1]["rrf_score"],
                    item[1].get("dense_score", 0.0),
                    str(item[0]),
                ),
                reverse=True,
            )

        top_candidates = sorted_candidates[:limit]

        # 4. Fetch full chunk data from PostgreSQL ensuring strict database grounding
        candidate_ids = [c_id for c_id, _ in top_candidates]
        db_res = await db.execute(
            select(KnowledgeChunk)
            .options(selectinload(KnowledgeChunk.source))
            .where(KnowledgeChunk.id.in_(candidate_ids))
        )
        loaded_chunks = {c.id: c for c in db_res.scalars().all()}

        evidence_items: list[EvidenceItem] = []
        for fusion_rank, (c_id, info) in enumerate(top_candidates, start=1):
            db_chunk = loaded_chunks.get(c_id)
            if db_chunk is None:
                continue

            # Create clean excerpt (first 300 chars or sentence)
            content = db_chunk.content.strip()
            excerpt = content[:280] + "..." if len(content) > 280 else content

            source_title = (
                db_chunk.source.title if db_chunk.source else "W3C Accessibility Standard"
            )
            final_score = (
                info["rrf_score"]
                if mode == "hybrid"
                else (
                    info["dense_score"]
                    if mode == "dense"
                    else float(info.get("lexical_score", 1.0))
                )
            )

            evidence_items.append(
                EvidenceItem(
                    chunk_id=db_chunk.id,
                    chunk_key=db_chunk.chunk_key,
                    criterion_id=db_chunk.criterion_id,
                    criterion_level=db_chunk.criterion_level,
                    title=db_chunk.section_title,
                    source_title=source_title,
                    source_url=db_chunk.source_url,
                    content_type=db_chunk.content_type,
                    excerpt=excerpt,
                    dense_rank=info.get("dense_rank"),
                    lexical_rank=info.get("lexical_rank"),
                    fusion_rank=fusion_rank if mode == "hybrid" else None,
                    score=round(final_score, 6),
                    metadata=db_chunk.chunk_metadata,
                )
            )

        return evidence_items, len(candidate_fusion), False
