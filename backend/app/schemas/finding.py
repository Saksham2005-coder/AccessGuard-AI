"""Pydantic schemas for accessibility findings and audited node targets."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FindingNodeResponse(BaseModel):
    """Specific DOM element node associated with an accessibility finding."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    target: list[str] = Field(default_factory=list)
    html_snippet: str | None = None
    failure_summary: str | None = None
    screenshot_reference: str | None = None


class FindingResponse(BaseModel):
    """Normalized finding item detected during an accessibility scan."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    scan_page_id: uuid.UUID
    axe_rule_id: str
    impact: str | None = None
    description: str
    help: str | None = None
    help_url: str | None = None
    wcag_tags: list[str] = Field(default_factory=list)
    selector: str | None = None
    html_snippet: str | None = None
    failure_summary: str | None = None
    fingerprint: str
    is_incomplete: bool = False
    created_at: datetime
    updated_at: datetime


class FindingDetailResponse(FindingResponse):
    """Detailed finding response with associated element nodes."""

    nodes: list[FindingNodeResponse] = Field(default_factory=list)


class FindingListResponse(BaseModel):
    """Paginated collection of accessibility findings."""

    items: list[FindingResponse]
    total: int
