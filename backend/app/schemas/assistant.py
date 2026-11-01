"""Pydantic schemas for Conversational Accessibility Assistant.

Phase 19 Feature 8: Schemas for chat queries, grounded assistant responses,
evidence citations, observed facts, and conversation history.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class FindingEvidenceItem(BaseModel):
    """Reference to an authorized scan finding grounding an answer."""

    finding_id: uuid.UUID
    rule_id: str
    impact: str | None = None
    selector: str | None = None
    description: str


class WcagCitationItem(BaseModel):
    """Authoritative WCAG criterion cited by the assistant."""

    criterion_id: str
    title: str
    guidance: str
    url: str | None = None


class AssistantStructuredData(BaseModel):
    """Structured evidence, citations, observations, and disclaimers."""

    evidence_findings: list[FindingEvidenceItem] = Field(default_factory=list)
    wcag_citations: list[WcagCitationItem] = Field(default_factory=list)
    observed_facts: list[str] = Field(default_factory=list)
    guidance_notes: list[str] = Field(default_factory=list)
    suggested_action: str | None = None
    limitations_notice: str = (
        "Automated accessibility assessment evaluates a subset of WCAG 2.2 criteria. "
        "Manual evaluation with assistive technologies (screen readers, keyboard traversal) "
        "is required for complete conformance verification."
    )


class AssistantChatRequest(BaseModel):
    """Query payload sent to the accessibility assistant."""

    project_id: uuid.UUID
    scan_id: uuid.UUID | None = None
    conversation_id: uuid.UUID | None = None
    message: str = Field(..., min_length=1, max_length=2000)


class AssistantMessageResponse(BaseModel):
    """Individual dialogue turn in an assistant conversation."""

    id: uuid.UUID
    conversation_id: uuid.UUID
    role: str
    content: str
    structured_data: AssistantStructuredData | None = None
    created_at: datetime


class AssistantConversationResponse(BaseModel):
    """Summary of a stored assistant conversation."""

    id: uuid.UUID
    project_id: uuid.UUID
    scan_id: uuid.UUID | None
    title: str
    created_at: datetime
    updated_at: datetime
    messages: list[AssistantMessageResponse] = Field(default_factory=list)
