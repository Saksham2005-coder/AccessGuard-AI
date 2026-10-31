"""Audit log persistence helper for LangGraph multi-agent execution."""

import time
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.workflow.state import AccessGuardGraphState
from app.core.logging import censor_sensitive_dict, get_logger
from app.db.models.agent_run import AgentRun

logger = get_logger("workflow_persistence")


async def record_agent_run(
    db: AsyncSession,
    *,
    scan_id: uuid.UUID | str,
    finding_id: uuid.UUID | str | None,
    agent_name: str,
    status: str,
    input_summary: dict[str, Any],
    output_summary: dict[str, Any],
    provider: str | None = None,
    model_name: str | None = None,
    prompt_version: str | None = None,
    duration_ms: int | None = None,
    error_code: str | None = None,
) -> AgentRun:
    """Persist structured agent execution audit record without secrets or private full DOM."""
    # Convert IDs to UUID instances
    scan_uuid = uuid.UUID(str(scan_id)) if isinstance(scan_id, str) else scan_id
    finding_uuid = (
        uuid.UUID(str(finding_id)) if finding_id and isinstance(finding_id, str) else finding_id
    )

    # Sanitize summaries to guarantee no API keys or sensitive auth tokens are persisted
    safe_input = censor_sensitive_dict(input_summary)
    safe_output = censor_sensitive_dict(output_summary)

    agent_run = AgentRun(
        scan_id=scan_uuid,
        finding_id=finding_uuid,
        agent_name=agent_name,
        status=status,
        input_summary=safe_input,
        output_summary=safe_output,
        provider=provider,
        model_name=model_name,
        prompt_version=prompt_version,
        duration_ms=duration_ms,
        error_code=error_code,
    )

    db.add(agent_run)
    await db.flush()

    logger.info(
        "Persisted agent execution run record",
        agent_name=agent_name,
        scan_id=str(scan_uuid),
        finding_id=str(finding_uuid) if finding_uuid else None,
        status=status,
        duration_ms=duration_ms,
    )
    return agent_run


async def persist_workflow_run_record(
    db: AsyncSession,
    state: AccessGuardGraphState,
    start_time: float,
) -> AgentRun | None:
    """Helper to persist the overall LangGraph investigation execution record from final state."""
    scan_id = state.get("scan_id")
    if not scan_id:
        return None

    duration_ms = int((time.monotonic() - start_time) * 1000)
    metadata = state.get("metadata", {})
    finding = state.get("finding", {})

    input_summary = {
        "axe_rule_id": finding.get("axe_rule_id"),
        "impact": finding.get("impact"),
        "selector": finding.get("selector"),
        "evidence_count": len(state.get("retrieved_evidence", [])),
    }

    output_summary: dict[str, Any] = {
        "status": state.get("status"),
        "attempt_count": state.get("attempt_count", 0),
        "has_analysis": state.get("analysis") is not None,
        "has_remediation": state.get("remediation_proposal") is not None,
    }
    review_result = state.get("review_result")
    if review_result:
        output_summary["accepted_for_human_review"] = review_result.get("accepted_for_human_review")

    first_error = state.get("errors", [{}])[0] if state.get("errors") else {}
    error_code = first_error.get("node")

    return await record_agent_run(
        db,
        scan_id=scan_id,
        finding_id=state.get("finding_id"),
        agent_name="remediation_workflow",
        status=state.get("status", "completed"),
        input_summary=input_summary,
        output_summary=output_summary,
        provider=metadata.get("remediation_provider") or metadata.get("analysis_provider"),
        model_name=metadata.get("remediation_model") or metadata.get("analysis_model"),
        prompt_version=metadata.get("remediation_prompt_version")
        or metadata.get("analysis_prompt_version"),
        duration_ms=duration_ms,
        error_code=error_code,
    )
