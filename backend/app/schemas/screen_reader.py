"""Pydantic schemas for screen-reader-oriented page reading preview and semantic analysis."""

from typing import Any, Literal

from pydantic import BaseModel, Field


class SemanticNode(BaseModel):
    """Individual node extracted from browser accessibility semantics and reading sequence."""

    sequence_index: int
    role: str
    accessible_name: str | None = None
    description: str | None = None
    heading_level: int | None = None
    landmark_type: str | None = None
    is_interactive: bool = False
    selector: str
    tag_name: str
    has_name: bool = True
    attributes: dict[str, Any] = Field(default_factory=dict)
    associated_finding_id: str | None = None
    potential_issue: str | None = None


class HeadingOutlineItem(BaseModel):
    """Heading outline element with hierarchy validation."""

    level: int
    text: str
    sequence_index: int
    selector: str
    is_skipped: bool = False


class LandmarkOutlineItem(BaseModel):
    """Structural landmark boundary extracted from HTML5 or ARIA."""

    landmark_type: str
    accessible_name: str | None = None
    sequence_index: int
    selector: str


class ReviewHint(BaseModel):
    """Heuristic accessibility review hint for potential usability or semantic gaps."""

    category: Literal["missing_name", "heading_skip", "duplicate_name", "generic_role"]
    message: str
    severity: Literal["warning", "advisory"]
    sequence_index: int
    selector: str
    associated_finding_id: str | None = None


class ScreenReaderSimulationResponse(BaseModel):
    """Complete structured screen-reader-oriented reading preview for an audited page."""

    scan_id: str
    page_id: str
    page_url: str
    nodes_count: int
    reading_order: list[SemanticNode] = Field(default_factory=list)
    headings: list[HeadingOutlineItem] = Field(default_factory=list)
    landmarks: list[LandmarkOutlineItem] = Field(default_factory=list)
    interactive_elements: list[SemanticNode] = Field(default_factory=list)
    review_hints: list[ReviewHint] = Field(default_factory=list)
    disclaimer: str = (
        "Screen-reader-oriented reading and navigation preview exposing DOM semantics and reading order. "
        "This browser-based preview does NOT emulate NVDA, JAWS, or VoiceOver execution across operating systems. "
        "Automated accessibility results are not a formal legal WCAG certification."
    )
    limitations: list[str] = Field(default_factory=list)
    captured_at: str
