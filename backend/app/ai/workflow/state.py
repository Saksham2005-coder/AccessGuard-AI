"""Typed state definition for AccessGuard AI LangGraph workflows."""

from typing import Any, TypedDict


class AccessGuardGraphState(TypedDict, total=False):
    """Shared immutable state passed across LangGraph nodes for accessibility investigation."""

    # Context identifiers
    scan_id: str
    finding_id: str
    user_id: str
    target_url: str

    # Normalized input finding payload
    finding: dict[str, Any]

    # Grounded RAG knowledge
    retrieved_evidence: list[dict[str, Any]]
    evidence_sufficient: bool

    # Agent outputs
    analysis: dict[str, Any] | None
    remediation_proposal: dict[str, Any] | None
    review_result: dict[str, Any] | None

    # Human-in-the-loop and validation
    human_decision: dict[str, Any] | None
    validation_result: dict[str, Any] | None

    # Lifecycle state
    status: str
    attempt_count: int
    errors: list[dict[str, Any]]
    metadata: dict[str, Any]
