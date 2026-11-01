"""Pydantic schemas for Responsive Accessibility Testing.

Phase 19 Feature 9: Viewport profile validation, multi-viewport audit requests,
shared vs unique violation diffs, and responsive matrix reporting.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ViewportProfile(BaseModel):
    """Specification for a responsive testing viewport."""

    name: str = Field(..., min_length=1, max_length=50, description="Profile label (desktop, tablet, mobile)")
    width: int = Field(..., ge=320, le=3840, description="CSS pixel width")
    height: int = Field(..., ge=480, le=2160, description="CSS pixel height")
    device_scale_factor: float = Field(1.0, ge=0.5, le=4.0)
    is_mobile: bool = False


class ViewportFindingDiff(BaseModel):
    """Violation item indicating across which viewports it was detected."""

    rule_id: str
    impact: str
    selector: str | None = None
    description: str
    viewports_detected: list[str]
    is_shared_across_all: bool


class ViewportRunSummary(BaseModel):
    """Summary of findings and severity counts for a single viewport run."""

    id: uuid.UUID
    viewport_name: str
    width: int
    height: int
    status: str
    total_violations: int
    critical_count: int
    serious_count: int
    moderate_count: int
    minor_count: int
    unique_violations_count: int


class ResponsiveMatrixReport(BaseModel):
    """Matrix comparing accessibility outcomes across multiple viewports."""

    scan_id: uuid.UUID
    target_url: str
    viewport_runs: list[ViewportRunSummary]
    shared_findings: list[ViewportFindingDiff]
    viewport_specific_findings: list[ViewportFindingDiff]
    tested_at: datetime


class RunResponsiveMatrixRequest(BaseModel):
    """Request payload to execute or evaluate a multi-viewport test matrix."""

    viewports: list[ViewportProfile] | None = Field(
        None,
        description="Optional custom profiles; defaults to Desktop, Tablet, and Mobile if omitted.",
    )
