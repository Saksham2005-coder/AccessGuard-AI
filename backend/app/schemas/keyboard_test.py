"""Pydantic schemas for Keyboard Navigation Simulator.

Phase 19 Feature 5: Deterministic keyboard-only navigation testing,
activeElement tracking, focus indicator evidence, and trap detection.
"""

from typing import Any

from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    """Bounding box for focused element."""
    x: float
    y: float
    width: float
    height: float


class ComputedFocusStyle(BaseModel):
    """Computed CSS styles related to focus visibility."""
    outline_style: str = "none"
    outline_width: str = "0px"
    outline_color: str = ""
    outline_offset: str = "0px"
    box_shadow: str = "none"
    border_style: str = "none"
    border_width: str = "0px"
    border_color: str = ""


class KeyboardStep(BaseModel):
    """Single observed step in the keyboard navigation traversal."""
    step_index: int = Field(..., description="1-indexed step number")
    action: str = Field(..., description="Key action executed: Tab, Shift+Tab, Escape")
    selector: str = Field(..., description="CSS selector or stable path")
    tag_name: str = Field(..., description="HTML tag name in lowercase")
    role: str | None = Field(default=None, description="Explicit or implicit ARIA role")
    accessible_name: str | None = Field(default=None, description="Computed accessible name")
    tabindex: int | None = Field(default=None, description="Tabindex attribute value if present")
    bounding_box: BoundingBox | None = Field(default=None, description="Element bounding box")
    is_clipped_or_offscreen: bool = Field(False, description="Whether element is outside viewport or zero-size")
    has_visible_focus_indicator: bool = Field(True, description="Whether an active focus indicator was detected")
    focus_style: ComputedFocusStyle | None = Field(default=None, description="Computed focus styling evidence")
    focus_notes: str | None = Field(default=None, description="Observation or manual review hint")


class KeyboardIssue(BaseModel):
    """Potential accessibility defect or manual review hint observed during keyboard traversal."""
    issue_type: str = Field(
        ...,
        description=(
            "missing_accessible_name | missing_focus_indicator | potential_focus_trap | "
            "positive_tabindex | offscreen_focus | reverse_traversal_mismatch"
        ),
    )
    severity: str = Field(..., description="critical | serious | moderate | minor | review_hint")
    step_index: int | None = Field(None, description="Step index where issue was detected")
    selector: str = Field(..., description="Target element selector")
    message: str = Field(..., description="Clear explanation of the observed keyboard behavior")
    recommendation: str = Field(..., description="Remediation guidance")
    wcag_criteria: list[str] = Field(default_factory=list, description="Associated WCAG success criteria")


class KeyboardNavigationSummary(BaseModel):
    """Summary metrics of the keyboard navigation test run."""
    total_steps: int = 0
    forward_steps: int = 0
    reverse_steps: int = 0
    unique_elements: int = 0
    issues_count: int = 0
    has_potential_trap: bool = False
    missing_indicator_count: int = 0
    missing_name_count: int = 0
    positive_tabindex_count: int = 0
    completion_status: str = Field(
        "completed",
        description="completed | capped | timed_out | failed",
    )


class KeyboardNavigationReport(BaseModel):
    """Complete results of a deterministic keyboard navigation test."""
    scan_id: str
    page_id: str
    page_url: str
    viewport: dict[str, int] = Field(default_factory=lambda: {"width": 1280, "height": 800})
    summary: KeyboardNavigationSummary
    steps: list[KeyboardStep] = Field(default_factory=list)
    reverse_steps: list[KeyboardStep] = Field(default_factory=list)
    issues: list[KeyboardIssue] = Field(default_factory=list)
    disclaimer: str = Field(
        default=(
            "Automated keyboard interaction test. Simulates standard Tab and Shift+Tab browser focus "
            "traversal under isolated conditions. This automated evidence aids manual testing and does "
            "not replace comprehensive manual keyboard verification or assistive technology."
        )
    )
    tested_at: str
    extra_metadata: dict[str, Any] = Field(default_factory=dict)
