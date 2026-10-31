"""Pydantic schemas for WCAG RAG search, candidate evidence, and citation provenance."""

import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class EvidenceItem(BaseModel):
    """Structured grounding evidence retrieved from official WCAG/ARIA knowledge base."""

    model_config = ConfigDict(from_attributes=True)

    chunk_id: uuid.UUID
    chunk_key: str
    criterion_id: str | None = None
    criterion_level: str | None = None
    title: str | None = None
    source_title: str
    source_url: str
    content_type: str
    excerpt: str
    dense_rank: int | None = None
    lexical_rank: int | None = None
    fusion_rank: int | None = None
    score: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class KnowledgeSearchRequest(BaseModel):
    """Request payload for semantic and hybrid knowledge retrieval."""

    query: str = Field(..., min_length=1, max_length=1000)
    criterion_id: str | None = Field(None, max_length=30)
    limit: int = Field(5, ge=1, le=50)
    retrieval_mode: str = Field("hybrid", pattern="^(hybrid|dense|lexical)$")


class KnowledgeSearchResponse(BaseModel):
    """Retrieval response containing ranked evidence items and abstention status."""

    query: str
    retrieval_mode: str
    evidence: list[EvidenceItem]
    total_candidates: int
    abstain: bool = False
    abstain_reason: str | None = None


class KnowledgeSourceResponse(BaseModel):
    """Public metadata for an indexed accessibility standard source."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source_key: str
    title: str
    source_url: str
    publisher: str
    standard_version: str | None = None
    content_version: str | None = None
    is_active: bool
