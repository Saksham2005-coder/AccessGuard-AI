"""Citation validation and evidence grounding against authoritative knowledge base."""

import uuid
from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.logging import get_logger
from app.db.models.knowledge import KnowledgeChunk
from app.schemas.rag import EvidenceItem

logger = get_logger("citation_validator")


@dataclass
class VerifiedCitation:
    """Canonical citation reference strictly verified against database provenance."""

    chunk_id: uuid.UUID
    chunk_key: str
    criterion_id: str | None
    section_title: str | None
    canonical_source_url: str
    source_title: str


@dataclass
class CitationValidationResult:
    """Outcome of citation verification against stored database records."""

    is_valid: bool
    verified_citations: list[VerifiedCitation] = field(default_factory=list)
    unverified_chunk_ids: list[uuid.UUID] = field(default_factory=list)
    unsupported_criteria: list[str] = field(default_factory=list)
    should_abstain: bool = False
    rejection_reason: str | None = None


class CitationValidator:
    """Enforces that AI remediation explanations only cite verified database knowledge."""

    @staticmethod
    async def validate_citations(
        db: AsyncSession,
        cited_chunk_ids: list[uuid.UUID],
        claimed_criterion_ids: list[str] | None = None,
    ) -> CitationValidationResult:
        """Verify cited chunk IDs exist in database and match official stored URLs."""
        if not cited_chunk_ids:
            return CitationValidationResult(
                is_valid=False,
                should_abstain=True,
                rejection_reason="No citation references were provided.",
            )

        stmt = (
            select(KnowledgeChunk)
            .options(selectinload(KnowledgeChunk.source))
            .where(KnowledgeChunk.id.in_(cited_chunk_ids))
        )
        res = await db.execute(stmt)
        found_chunks = {c.id: c for c in res.scalars().all()}

        verified: list[VerifiedCitation] = []
        unverified: list[uuid.UUID] = []

        for cid in cited_chunk_ids:
            chunk = found_chunks.get(cid)
            if chunk is not None:
                verified.append(
                    VerifiedCitation(
                        chunk_id=chunk.id,
                        chunk_key=chunk.chunk_key,
                        criterion_id=chunk.criterion_id,
                        section_title=chunk.section_title,
                        canonical_source_url=chunk.source_url,
                        source_title=chunk.source.title
                        if chunk.source
                        else "W3C Accessibility Standard",
                    )
                )
            else:
                unverified.append(cid)

        # Check for unverified citations
        if unverified:
            logger.warning(
                "Detected unverified citation references",
                unverified_count=len(unverified),
                ids=[str(x) for x in unverified],
            )
            return CitationValidationResult(
                is_valid=False,
                verified_citations=verified,
                unverified_chunk_ids=unverified,
                should_abstain=True,
                rejection_reason=(
                    f"Model generated {len(unverified)} citation ID(s) that do not exist in the database."
                ),
            )

        # Check if claimed criterion IDs are supported by the verified citations
        unsupported: list[str] = []
        if claimed_criterion_ids:
            cited_criteria = {v.criterion_id for v in verified if v.criterion_id}
            for claimed in claimed_criterion_ids:
                if claimed and claimed not in cited_criteria:
                    unsupported.append(claimed)

        if unsupported:
            return CitationValidationResult(
                is_valid=False,
                verified_citations=verified,
                unsupported_criteria=unsupported,
                should_abstain=True,
                rejection_reason=(
                    f"Claimed criteria {unsupported} are not grounded in cited knowledge chunks."
                ),
            )

        return CitationValidationResult(
            is_valid=True,
            verified_citations=verified,
            unverified_chunk_ids=[],
            unsupported_criteria=[],
            should_abstain=False,
        )

    @staticmethod
    def check_abstention_threshold(evidence: list[EvidenceItem], min_score: float = 0.005) -> bool:
        """Determine whether evidence is sufficient or system should abstain."""
        if not evidence:
            return True
        top_score = max((item.score for item in evidence), default=0.0)
        return top_score < min_score
