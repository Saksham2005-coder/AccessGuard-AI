"""API endpoints for WCAG knowledge search, criterion inspection, and official sources."""

from typing import Any

from fastapi import APIRouter
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.deps import CurrentUserDep, DbDep
from app.core.errors import NotFoundError
from app.core.logging import get_logger
from app.db.models.knowledge import KnowledgeChunk, KnowledgeSource
from app.rag.citation_validator import CitationValidator
from app.rag.retriever import HybridRetriever
from app.schemas.rag import (
    EvidenceItem,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    KnowledgeSourceResponse,
)

router = APIRouter(prefix="/knowledge", tags=["knowledge"])
logger = get_logger("knowledge_api")

_retriever = HybridRetriever()


@router.get("/sources", response_model=list[KnowledgeSourceResponse])
async def list_knowledge_sources(db: DbDep) -> Any:
    """List all indexed official accessibility standards and guideline sources."""
    result = await db.execute(
        select(KnowledgeSource)
        .where(KnowledgeSource.is_active.is_(True))
        .order_by(KnowledgeSource.source_key.asc())
    )
    sources = result.scalars().all()
    return sources


@router.post("/search", response_model=KnowledgeSearchResponse)
async def search_knowledge(
    request: KnowledgeSearchRequest,
    db: DbDep,
    current_user: CurrentUserDep,
) -> Any:
    """Search WCAG and WAI standards using dense, lexical, or hybrid reciprocal rank fusion."""
    logger.info("Knowledge search requested", user_id=str(current_user.id), query=request.query)
    evidence, total_candidates, should_abstain = await _retriever.search(
        db=db,
        query=request.query,
        criterion_id=request.criterion_id,
        limit=request.limit,
        mode=request.retrieval_mode,
    )

    abstain_by_threshold = CitationValidator.check_abstention_threshold(evidence)
    final_abstain = should_abstain or abstain_by_threshold

    return KnowledgeSearchResponse(
        query=request.query,
        retrieval_mode=request.retrieval_mode,
        evidence=evidence if not final_abstain else [],
        total_candidates=total_candidates,
        abstain=final_abstain,
        abstain_reason="Insufficient evidence threshold met for query." if final_abstain else None,
    )


@router.get("/criteria/{criterion_id}", response_model=list[EvidenceItem])
async def get_criterion_details(criterion_id: str, db: DbDep) -> Any:
    """Retrieve all normative statement chunks, understanding guidance, and techniques for a criterion ID."""
    clean_id = criterion_id.strip()
    result = await db.execute(
        select(KnowledgeChunk)
        .options(selectinload(KnowledgeChunk.source))
        .where(KnowledgeChunk.criterion_id == clean_id)
        .order_by(KnowledgeChunk.content_type.asc())
    )
    chunks = result.scalars().all()

    if not chunks:
        raise NotFoundError(f"WCAG criterion '{criterion_id}' not found in knowledge base.")

    items: list[EvidenceItem] = []
    for chunk in chunks:
        source_title = chunk.source.title if chunk.source else "W3C Accessibility Standard"
        items.append(
            EvidenceItem(
                chunk_id=chunk.id,
                chunk_key=chunk.chunk_key,
                criterion_id=chunk.criterion_id,
                criterion_level=chunk.criterion_level,
                title=chunk.section_title,
                source_title=source_title,
                source_url=chunk.source_url,
                content_type=chunk.content_type,
                excerpt=chunk.content[:280] + "..." if len(chunk.content) > 280 else chunk.content,
                score=1.0,
                metadata=chunk.chunk_metadata,
            )
        )
    return items
