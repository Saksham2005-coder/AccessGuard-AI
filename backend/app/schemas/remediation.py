"""Pydantic schemas for remediation proposals, human approvals, and snapshot validations."""

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class RemediationDecisionRequest(BaseModel):
    """Payload for human approval or rejection of a proposed remediation."""

    decision: Literal["approved", "rejected"] = Field(
        ...,
        description="Review decision: 'approved' or 'rejected'.",
    )
    comments: str | None = Field(
        default=None,
        max_length=2000,
        description="Optional human reviewer notes or explanation.",
    )


class RemediationApprovalResponse(BaseModel):
    """Audit record schema for human approval decisions."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    remediation_id: uuid.UUID
    reviewer_id: uuid.UUID
    decision: str
    comments: str | None = None
    created_at: datetime


class ValidationResultResponse(BaseModel):
    """Audit record schema for isolated DOM snapshot validation outcomes."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    remediation_id: uuid.UUID
    validation_mode: str
    passed: bool
    original_rule_resolved: bool
    new_violations: list[dict[str, Any]] = Field(default_factory=list)
    details: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class RemediationResponse(BaseModel):
    """Complete remediation proposal schema including audit trails."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    finding_id: uuid.UUID
    status: str
    root_cause: str
    recommendation: str
    patch_format: str
    patch_payload: dict[str, Any] = Field(default_factory=dict)
    before_snippet: str | None = None
    after_snippet: str | None = None
    confidence: float | None = None
    model_provider: str | None = None
    model_name: str | None = None
    prompt_version: str | None = None
    approvals: list[RemediationApprovalResponse] = Field(default_factory=list)
    validation_results: list[ValidationResultResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class ComparisonResponse(BaseModel):
    """Isolated DOM snapshot comparison schema with before/after visual and structural diffs."""

    model_config = ConfigDict(from_attributes=True)

    remediation_id: uuid.UUID
    finding_id: uuid.UUID
    rule_id: str
    before_html: str
    after_html: str
    before_screenshot_url: str | None = None
    after_screenshot_url: str | None = None
    dom_diff: str
    patch_operations: list[dict[str, Any]] = Field(default_factory=list)
    original_rule_resolved: bool
    new_violations: list[dict[str, Any]] = Field(default_factory=list)
    passed: bool
    status: str
    created_at: datetime
    details: dict[str, Any] = Field(default_factory=dict)

