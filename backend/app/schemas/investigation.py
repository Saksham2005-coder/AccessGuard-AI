"""Pydantic schemas for autonomous accessibility agent investigations and synthesis."""

from typing import Literal

from pydantic import BaseModel, Field

ConfidenceLevel = Literal["supported", "tentative", "insufficient_evidence"]
InvestigationStatus = Literal["completed", "partial", "skipped", "failed"]
PriorityLevel = Literal["P1", "P2", "P3", "P4"]


class Observation(BaseModel):
    """Specific observation produced by a specialist agent grounded in scan findings."""

    finding_id: str | None = None
    rule_id: str
    selector: str | None = None
    summary: str
    details: str | None = None
    severity: str | None = None


class Recommendation(BaseModel):
    """Actionable remediation recommendation with priority and code hint."""

    title: str
    action: str
    code_example: str | None = None
    priority: PriorityLevel
    affected_finding_ids: list[str] = Field(default_factory=list)


class SpecialistReport(BaseModel):
    """Structured report returned by a specialist agent for a specific accessibility dimension."""

    agent_id: str
    agent_name: str
    agent_version: str = "1.0.0"
    dimension: str
    status: InvestigationStatus
    confidence: ConfidenceLevel
    findings_count: int = 0
    observations: list[Observation] = Field(default_factory=list)
    recommendations: list[Recommendation] = Field(default_factory=list)
    wcag_criteria: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    evidence_references: list[str] = Field(default_factory=list)


class WcagCitation(BaseModel):
    """WCAG 2.2 criterion reference grounded in W3C standards."""

    criterion_id: str
    title: str
    level: str = "AA"
    summary: str
    url: str | None = None


class RemediationMatrixItem(BaseModel):
    """Item in the prioritized remediation matrix synthesized across specialists."""

    priority: PriorityLevel
    title: str
    description: str
    dimension: str
    affected_findings: list[str] = Field(default_factory=list)
    remediation_hint: str


class InvestigationReport(BaseModel):
    """Comprehensive investigation report synthesizing all specialist evaluations."""

    investigation_id: str
    scan_id: str
    status: InvestigationStatus
    overall_confidence: ConfidenceLevel
    executive_summary: str
    specialists: dict[str, SpecialistReport]
    remediation_matrix: list[RemediationMatrixItem] = Field(default_factory=list)
    manual_verification_checklist: list[str] = Field(default_factory=list)
    wcag_citations: list[WcagCitation] = Field(default_factory=list)
    duration_ms: int | None = None
    created_at: str


class InvestigationRunSummary(BaseModel):
    """Lightweight summary of an investigation run."""

    id: str
    scan_id: str
    status: str
    overall_confidence: str
    executive_summary: str
    created_at: str


class InvestigationListResponse(BaseModel):
    """List response for past investigations of a scan."""

    items: list[InvestigationRunSummary]
    total: int


class TriggerInvestigationRequest(BaseModel):
    """Request payload to trigger an investigation."""

    force_refresh: bool = False
    custom_instructions: str | None = None
