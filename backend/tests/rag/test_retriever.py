"""Unit tests for hybrid, dense, and lexical retrieval with Reciprocal Rank Fusion (RRF)."""

import pytest
from qdrant_client import QdrantClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.knowledge import KnowledgeChunk, KnowledgeSource
from app.rag.embeddings import EmbeddingService
from app.rag.retriever import HybridRetriever, tokenize_for_bm25
from app.rag.vector_store import QdrantVectorStore


def test_tokenize_for_bm25() -> None:
    """Verify tokenizer preserves criterion dotted IDs and hyphenated attribute names."""
    tokens = tokenize_for_bm25("Check WCAG 1.4.3 color-contrast and aria-label requirements")
    assert "1.4.3" in tokens
    assert "color-contrast" in tokens
    assert "aria-label" in tokens


@pytest.fixture
async def seeded_rag_db(db_session: AsyncSession) -> tuple[QdrantVectorStore, list[KnowledgeChunk]]:
    """Seed test database and in-memory Qdrant with known WCAG criteria."""
    source = KnowledgeSource(
        source_key="wcag22_test",
        title="WCAG 2.2 Recommendation",
        source_url="https://www.w3.org/TR/WCAG22/",
        publisher="W3C",
        standard_version="WCAG 2.2",
    )
    db_session.add(source)
    await db_session.flush()

    chunks_data = [
        (
            "wcag22_sc_1_1_1",
            "1.1.1",
            "A",
            "Perceivable",
            "1.1.1 Non-text Content (Level A)",
            "All non-text content that is presented to the user has a text alternative that serves the equivalent purpose.",
            "https://www.w3.org/TR/WCAG22/#non-text-content",
        ),
        (
            "wcag22_sc_1_4_3",
            "1.4.3",
            "AA",
            "Perceivable",
            "1.4.3 Contrast (Minimum) (Level AA)",
            "The visual presentation of text and images of text has a contrast ratio of at least 4.5:1.",
            "https://www.w3.org/TR/WCAG22/#contrast-minimum",
        ),
        (
            "wcag22_sc_2_1_1",
            "2.1.1",
            "A",
            "Operable",
            "2.1.1 Keyboard (Level A)",
            "All functionality of the content is operable through a keyboard interface without requiring specific timings for individual keystrokes.",
            "https://www.w3.org/TR/WCAG22/#keyboard",
        ),
        (
            "wcag22_sc_4_1_2",
            "4.1.2",
            "A",
            "Robust",
            "4.1.2 Name, Role, Value (Level A)",
            "For all user interface components, the name and role can be programmatically determined; states, properties, and values can be set programmatically.",
            "https://www.w3.org/TR/WCAG22/#name-role-value",
        ),
    ]

    persisted_chunks: list[KnowledgeChunk] = []
    qdrant = QdrantVectorStore(client=QdrantClient(":memory:"))
    embedder = EmbeddingService(use_mock=True)

    qdrant_points = []
    for c_key, cid, lvl, principle, title, text, url in chunks_data:
        chunk = KnowledgeChunk(
            source_id=source.id,
            chunk_key=c_key,
            criterion_id=cid,
            criterion_level=lvl,
            principle=principle,
            section_title=title,
            content_type="normative_criterion",
            content=text,
            source_url=url,
            chunk_metadata={"source_key": "wcag22_test"},
            content_hash=f"hash_{cid}",
            embedding_model="mock",
        )
        db_session.add(chunk)
        await db_session.flush()
        persisted_chunks.append(chunk)

        vec = embedder.embed_query(f"{title} {text}")
        qdrant_points.append(
            (
                chunk.id,
                vec,
                {
                    "chunk_id": str(chunk.id),
                    "chunk_key": c_key,
                    "criterion_id": cid,
                    "criterion_level": lvl,
                    "content_type": "normative_criterion",
                    "section_title": title,
                    "source_url": url,
                    "content": text,
                },
            )
        )

    qdrant.upsert_chunks(qdrant_points)
    await db_session.commit()
    return qdrant, persisted_chunks


@pytest.mark.asyncio
async def test_hybrid_retrieval_exact_identifier(
    db_session: AsyncSession,
    seeded_rag_db: tuple[QdrantVectorStore, list[KnowledgeChunk]],
) -> None:
    """Verify hybrid retriever prioritizes exact criterion ID lookups."""
    qdrant, _ = seeded_rag_db
    retriever = HybridRetriever(
        vector_store=qdrant,
        embedding_service=EmbeddingService(use_mock=True),
    )

    evidence, total, should_abstain = await retriever.search(
        db=db_session,
        query="1.4.3",
        limit=3,
        mode="hybrid",
    )

    assert not should_abstain
    assert total >= 1
    assert len(evidence) >= 1
    assert evidence[0].criterion_id == "1.4.3"
    assert "Contrast (Minimum)" in evidence[0].title
    assert evidence[0].source_url == "https://www.w3.org/TR/WCAG22/#contrast-minimum"


@pytest.mark.asyncio
async def test_lexical_retrieval_mode(
    db_session: AsyncSession,
    seeded_rag_db: tuple[QdrantVectorStore, list[KnowledgeChunk]],
) -> None:
    """Verify lexical BM25 retrieval finds keyword matches."""
    qdrant, _ = seeded_rag_db
    retriever = HybridRetriever(
        vector_store=qdrant,
        embedding_service=EmbeddingService(use_mock=True),
    )

    evidence, total, should_abstain = await retriever.search(
        db=db_session,
        query="keyboard interface keystrokes",
        limit=3,
        mode="lexical",
    )

    assert not should_abstain
    assert len(evidence) >= 1
    assert evidence[0].criterion_id == "2.1.1"


@pytest.mark.asyncio
async def test_retriever_abstains_on_empty_or_whitespace_query(
    db_session: AsyncSession,
    seeded_rag_db: tuple[QdrantVectorStore, list[KnowledgeChunk]],
) -> None:
    """Verify retriever safely abstains when query contains no search terms."""
    qdrant, _ = seeded_rag_db
    retriever = HybridRetriever(
        vector_store=qdrant,
        embedding_service=EmbeddingService(use_mock=True),
    )

    evidence, total, should_abstain = await retriever.search(
        db=db_session,
        query="    ",
        limit=5,
    )
    assert should_abstain is True
    assert len(evidence) == 0
