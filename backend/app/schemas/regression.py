"""Pydantic schemas for Accessibility Regression Monitoring.

Phase 19 Feature 6: Historical regression comparison, stable versioned finding fingerprints,
coverage awareness, pinned baselines, scheduled audits, and notifications.
"""

from typing import Any

from pydantic import BaseModel, Field


class RegressionFindingItem(BaseModel):
    """Normalized finding representation categorized under regression analysis."""
    finding_id: str
    page_url: str
    axe_rule_id: str
    impact: str | None = None
    description: str
    selector: str | None = None
    html_snippet: str | None = None
    wcag_tags: list[str] = Field(default_factory=list)
    classification: str = Field(
        ...,
        description="new | resolved | persistent | changed | inconclusive",
    )
    change_details: str | None = None
    fingerprint: str


class CoverageSummary(BaseModel):
    """Audit surface coverage comparison between baseline and target scan."""
    baseline_pages_count: int
    current_pages_count: int
    matched_pages_count: int
    missing_pages_count: int
    new_pages_count: int
    coverage_status: str = Field(
        ...,
        description="full | partial | inconclusive",
    )
    notes: list[str] = Field(default_factory=list)


class RegressionComparisonSummary(BaseModel):
    """Aggregate statistics for regression comparison."""
    new_count: int = 0
    resolved_count: int = 0
    persistent_count: int = 0
    changed_count: int = 0
    inconclusive_count: int = 0
    net_change: int = Field(0, description="new_count - resolved_count")
    has_critical_regression: bool = False


class RegressionComparisonReport(BaseModel):
    """Complete evidence-backed regression analysis between two scans."""
    project_id: str
    current_scan_id: str
    baseline_scan_id: str
    baseline_type: str = Field(
        ...,
        description="pinned | previous_successful | custom_selection",
    )
    current_scan_date: str
    baseline_scan_date: str
    coverage: CoverageSummary
    summary: RegressionComparisonSummary
    findings: list[RegressionFindingItem] = Field(default_factory=list)
    fingerprint_version: str = "v1"
    compared_at: str
    extra_metadata: dict[str, Any] = Field(default_factory=dict)


class ProjectBaselineResponse(BaseModel):
    """Designated project baseline scan response."""
    id: str
    project_id: str
    scan_id: str
    scan_date: str
    scan_target_url: str
    pinned_at: str
    notes: str | None = None


class SetBaselineRequest(BaseModel):
    """Request payload to pin a project baseline scan."""
    scan_id: str
    notes: str | None = None


class ScanScheduleCreate(BaseModel):
    """Request payload to create a recurring scheduled audit."""
    cadence: str = Field("weekly", description="daily | weekly | biweekly | monthly")
    target_url: str
    notify_on_regression: bool = True


class ScanScheduleResponse(BaseModel):
    """Scheduled audit configuration response."""
    id: str
    project_id: str
    cadence: str
    target_url: str
    is_active: bool
    last_run_at: str | None = None
    next_run_at: str | None = None
    notify_on_regression: bool
    created_at: str


class InAppNotificationResponse(BaseModel):
    """In-app alert response."""
    id: str
    title: str
    message: str
    notification_type: str
    link_url: str | None = None
    is_read: bool
    created_at: str
