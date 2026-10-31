"""Unit tests for citation validation and evidence grounding against database provenance."""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.knowledge import KnowledgeChunk, KnowledgeSource
from app.rag.citation_validator import CitationValidator


@pytest.fixture
async def sample_chunk(db_session: AsyncSession) -> KnowledgeChunk:
    """Create sample knowledge source and chunk."""
    source = KnowledgeSource(
        source_key="wcag_cite_test",
        title="WCAG Citation Test",
        source_url="https://www.w3.org/TR/WCAG22/",
        publisher="W3C",
    )
    db_session.add(source)
    await db_session.flush()

    chunk = KnowledgeChunk(
        source_id=source.id,
        chunk_key="wcag22_sc_1_1_1_test",
        criterion_id="1.1.1",
        criterion_level="A",
        section_title="1.1.1 Non-text Content",
        content_type="normative_criterion",
        content="Non-text content requires equivalent text alternatives.",
        source_url="https://www.w3.org/TR/WCAG22/#non-text-content",
        chunk_metadata={"source_key": "wcag_cite_test"},
        content_hash="dummy_hash_111",
        embedding_model="mock",
    )
    db_session.add(chunk)
    await db_session.commit()
    return chunk


@pytest.mark.asyncio
async def test_citation_validator_validates_existing_chunks(
    db_session: AsyncSession, sample_chunk: KnowledgeChunk
) -> None:
    """Verify valid chunk IDs return verified citation records with official URLs."""
    result = await CitationValidator.validate_citations(
        db=db_session,
        cited_chunk_ids=[sample_chunk.id],
        claimed_criterion_ids=["1.1.1"],
    )
    assert result.is_valid is True
    assert result.should_abstain is False
    assert len(result.verified_citations) == 1
    assert result.verified_citations[0].canonical_source_url == "https://www.w3.org/TR/WCAG22/#non-text-content"
    assert result.verified_citations[0].criterion_id == "1.1.1"


@pytest.mark.asyncio
async def test_citation_validator_rejects_hallucinated_chunk_id(
    db_session: AsyncSession, sample_chunk: KnowledgeChunk
) -> None:
    """Verify validator rejects citations referencing non-existent chunk IDs."""
    fake_id = uuid.uuid4()
    result = await CitationValidator.validate_citations(
        db=db_session,
        cited_chunk_ids=[sample_chunk.id, fake_id],
    )
    assert result.is_valid is False
    assert result.should_abstain is True
    assert fake_id in result.unverified_chunk_ids
    assert "do not exist in the database" in (result.rejection_reason or "")


@pytest.mark.asyncio
async def test_citation_validator_rejects_unsupported_criterion_claim(
    db_session: AsyncSession, sample_chunk: KnowledgeChunk
) -> None:
    """Verify validator rejects explanation when model claims criterion not in cited evidence."""
    result = await CitationValidator.validate_citations(
        db=db_session,
        cited_chunk_ids=[sample_chunk.id],  # only supports 1.1.1
        claimed_criterion_ids=["1.1.1", "2.4.7"],  # 2.4.7 is unsupported
    )
    assert result.is_valid is False
    assert result.should_abstain is True
    assert "2.4.7" in result.unsupported_criteria


@pytest.mark.asyncio
async def test_citation_validator_empty_citations_abstains(
    db_session: AsyncSession,
) -> None:
    """Verify validator abstains when empty citations list is given."""
    result = await CitationValidator.validate_citations(
        db=db_session,
        cited_chunk_ids=[],
    )
    assert result.is_valid is False
    assert result.should_abstain is True
