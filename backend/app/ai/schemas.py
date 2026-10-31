"""Pydantic schemas for typed structured LLM generation and remediation validation."""

import re
from typing import Literal

from pydantic import BaseModel, Field, field_validator

# Allowed DOM attributes for automated remediation patches
SAFE_ATTRIBUTES = {
    "alt",
    "aria-label",
    "aria-labelledby",
    "aria-describedby",
    "aria-hidden",
    "aria-expanded",
    "aria-haspopup",
    "aria-controls",
    "aria-live",
    "aria-atomic",
    "aria-required",
    "aria-invalid",
    "role",
    "title",
    "tabindex",
    "id",
    "lang",
    "scope",
}

DISALLOWED_ATTR_PATTERNS = [
    re.compile(r"^on[a-z]+", re.IGNORECASE),  # onclick, onload, etc.
    re.compile(
        r"^(href|src|action|formaction)$", re.IGNORECASE
    ),  # URLs must not be altered arbitrarily
]


class PatchOperation(BaseModel):
    """Constrained DOM operation for sandboxed snapshot remediation."""

    operation: Literal["set_attribute", "remove_attribute", "replace_text"]
    selector: str = Field(
        min_length=1, max_length=500, description="CSS selector for target element"
    )
    attribute: str | None = Field(
        default=None, max_length=100, description="Attribute name to set/remove"
    )
    value: str | None = Field(
        default=None, max_length=2000, description="Attribute value or replacement text"
    )

    @field_validator("attribute")
    @classmethod
    def validate_safe_attribute(cls, attr: str | None, _info: object = None) -> str | None:
        """Reject dangerous or event-handler attributes."""
        if attr is None:
            return None
        clean_attr = attr.strip().lower()
        for pat in DISALLOWED_ATTR_PATTERNS:
            if pat.search(clean_attr):
                raise ValueError(f"Attribute '{attr}' is prohibited in safe patch operations.")
        if clean_attr not in SAFE_ATTRIBUTES:
            raise ValueError(
                f"Attribute '{attr}' is not in the allowlist of safe accessibility attributes: {sorted(SAFE_ATTRIBUTES)}"
            )
        return clean_attr

    @field_validator("value")
    @classmethod
    def validate_safe_value(cls, val: str | None) -> str | None:
        """Reject javascript: or data: URIs in attribute values."""
        if val is None:
            return None
        clean_val = val.strip().lower()
        if "javascript:" in clean_val or "vbscript:" in clean_val:
            raise ValueError("Script schemes are forbidden in patch values.")
        return val


class FindingAnalysis(BaseModel):
    """Structured root cause analysis and criterion mapping for an accessibility finding."""

    summary: str = Field(
        min_length=10, max_length=1000, description="Concise explanation of the accessibility issue"
    )
    likely_root_cause: str = Field(
        min_length=10, max_length=1000, description="Underlying architectural or markup cause"
    )
    affected_element_type: str | None = Field(
        default=None, max_length=100, description="HTML tag or ARIA role"
    )
    relevant_criterion_ids: list[str] = Field(
        default_factory=list, description="WCAG criteria numbers (e.g. ['1.1.1', '1.4.3'])"
    )
    needs_manual_review: bool = Field(
        default=False,
        description="Flag indicating if finding cannot be verified without human test",
    )
    limitations: list[str] = Field(
        default_factory=list, max_length=10, description="Automated testing constraints"
    )
    evidence_chunk_ids: list[str] = Field(
        default_factory=list, description="UUID string IDs of cited knowledge chunks"
    )


class RemediationProposal(BaseModel):
    """Structured code remediation proposal with optional constrained DOM patch operations."""

    problem: str = Field(
        min_length=10,
        max_length=1000,
        description="Statement of the barrier for assistive technology",
    )
    recommendation: str = Field(
        min_length=10, max_length=2000, description="Guidance explaining how to resolve the issue"
    )
    before_snippet: str | None = Field(
        default=None, max_length=4000, description="Original problematic markup excerpt"
    )
    after_snippet: str | None = Field(
        default=None, max_length=4000, description="Corrected markup illustration"
    )
    patch_format: Literal["snippet", "dom_operations", "manual_steps"] = Field(
        default="snippet", description="Format of remediation proposal"
    )
    patch_operations: list[PatchOperation] = Field(
        default_factory=list, max_length=20, description="Bounded DOM mutations for snapshot test"
    )
    expected_effect: str = Field(
        min_length=5, max_length=1000, description="Anticipated effect on assistive tech"
    )
    manual_checks: list[str] = Field(
        default_factory=list,
        max_length=10,
        description="Manual verification steps developer should perform",
    )
    evidence_chunk_ids: list[str] = Field(
        default_factory=list, description="UUID string IDs of cited knowledge chunks"
    )
    model_confidence: float | None = Field(
        default=None, ge=0.0, le=1.0, description="Self-reported confidence score (0.0 to 1.0)"
    )


class ReviewResult(BaseModel):
    """Deterministic validation result verifying proposed remediation against safe policies."""

    accepted_for_human_review: bool = Field(
        description="True if proposal complies with all safety policies"
    )
    rejection_reasons: list[str] = Field(
        default_factory=list, description="Reasons for rejecting proposal"
    )
    evidence_complete: bool = Field(
        default=True, description="True if citations exist and match database records"
    )
    policy_checks_passed: list[str] = Field(
        default_factory=list, description="List of passed security and safety policies"
    )
    policy_checks_failed: list[str] = Field(
        default_factory=list, description="List of failed safety checks"
    )
