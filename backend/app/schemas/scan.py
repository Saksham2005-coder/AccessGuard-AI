"""Pydantic schemas for scan jobs, page audits, findings, and SSE event streams."""

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ScanCreateRequest(BaseModel):
    """Payload for initiating a new website accessibility scan."""

    target_url: str = Field(..., description="Root URL of verified website to audit")
    max_pages: int = Field(default=20, ge=1, le=100, description="Maximum pages to crawl")
    max_depth: int = Field(default=2, ge=0, le=5, description="Maximum link crawl depth")


class ScanResponse(BaseModel):
    """Structured representation of a scan job."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    requested_by: uuid.UUID
    target_url: str
    status: str
    config: dict[str, Any]
    started_at: datetime | None = None
    completed_at: datetime | None = None
    total_pages: int
    pages_succeeded: int
    pages_failed: int
    total_violations: int
    axe_version: str | None = None
    browser_version: str | None = None
    error_code: str | None = None
    error_summary: str | None = None
    created_at: datetime


class ScanListResponse(BaseModel):
    """Collection of scans."""

    items: list[ScanResponse]
    total: int


class ScanEventItem(BaseModel):
    """Progress event emitted during scan execution."""

    sequence_number: int
    event_type: str
    payload: dict[str, Any]
    created_at: datetime
