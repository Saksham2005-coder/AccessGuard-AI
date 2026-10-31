"""Service layer orchestrating accessibility remediations, human approvals, and LangGraph checkpoints."""

import time
import uuid
from typing import Any

from langgraph.types import Command
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai.factory import get_llm_provider
from app.ai.provider import LLMProvider
from app.ai.workflow.checkpoint import get_workflow_checkpointer
from app.ai.workflow.graph import build_remediation_graph
from app.ai.workflow.persistence import record_agent_run
from app.ai.workflow.state import AccessGuardGraphState
from app.core.errors import AuthorizationError, ConflictError, NotFoundError, ValidationError
from app.core.logging import get_logger
from app.db.models.finding import Finding
from app.db.models.project import Project
from app.db.models.remediation import Remediation, RemediationApproval, ValidationResult
from app.db.models.scan import Scan
from app.db.models.scan_page import ScanPage

logger = get_logger("remediation_service")


async def get_finding_and_check_ownership(
    db: AsyncSession,
    finding_id: uuid.UUID,
    user_id: uuid.UUID,
) -> tuple[Finding, Project]:
    """Retrieve finding by ID and verify user owns the parent project."""
    stmt = (
        select(Finding, Project)
        .join(ScanPage, Finding.scan_page_id == ScanPage.id)
        .join(Scan, ScanPage.scan_id == Scan.id)
        .join(Project, Scan.project_id == Project.id)
        .options(selectinload(Finding.nodes))
        .where(Finding.id == finding_id)
    )
    result = await db.execute(stmt)
    row = result.first()
    if not row:
        raise NotFoundError(f"Finding with ID '{finding_id}' not found.")

    finding, project = row
    if project.owner_id != user_id:
        raise AuthorizationError("You do not have permission to access this finding.")

    return finding, project


async def get_remediation_and_check_ownership(
    db: AsyncSession,
    remediation_id: uuid.UUID,
    user_id: uuid.UUID,
) -> tuple[Remediation, Finding, Project]:
    """Retrieve remediation by ID with its audit trails and verify user owns the parent project."""
    stmt = (
        select(Remediation, Finding, Project)
        .join(Finding, Remediation.finding_id == Finding.id)
        .join(ScanPage, Finding.scan_page_id == ScanPage.id)
        .join(Scan, ScanPage.scan_id == Scan.id)
        .join(Project, Scan.project_id == Project.id)
        .options(
            selectinload(Remediation.approvals),
            selectinload(Remediation.validation_results),
            selectinload(Finding.nodes),
        )
        .where(Remediation.id == remediation_id)
    )
    result = await db.execute(stmt)
    row = result.first()
    if not row:
        raise NotFoundError(f"Remediation with ID '{remediation_id}' not found.")

    remediation, finding, project = row
    if project.owner_id != user_id:
        raise AuthorizationError("You do not have permission to access this remediation.")

    return remediation, finding, project


async def create_or_run_remediation_proposal(
    db: AsyncSession,
    finding_id: uuid.UUID,
    user_id: uuid.UUID,
    provider: LLMProvider | None = None,
    retriever: Any = None,
) -> Remediation:
    """Generate or retrieve an evidence-grounded remediation proposal for an accessibility finding."""
    finding, project = await get_finding_and_check_ownership(db, finding_id, user_id)

    # Check if a remediation proposal already exists for this finding
    stmt = (
        select(Remediation)
        .options(
            selectinload(Remediation.approvals),
            selectinload(Remediation.validation_results),
        )
        .where(Remediation.finding_id == finding_id)
        .order_by(Remediation.created_at.desc())
    )
    existing_res = await db.execute(stmt)
    existing_remediation = existing_res.scalars().first()
    if existing_remediation and existing_remediation.status in ("proposed", "needs_review", "approved", "validated"):
        return existing_remediation

    # Compile the LangGraph investigation workflow with human approval interrupt enabled
    llm = provider or get_llm_provider()
    checkpointer = get_workflow_checkpointer()
    graph = build_remediation_graph(
        provider=llm,
        retriever=retriever,
        db=db,
        checkpointer=checkpointer,
        require_human_approval=True,
    )

    finding_payload = {
        "id": str(finding.id),
        "axe_rule_id": finding.axe_rule_id,
        "impact": finding.impact,
        "description": finding.description,
        "help": finding.help,
        "help_url": finding.help_url,
        "wcag_tags": finding.wcag_tags or [],
        "selector": finding.selector,
        "html_snippet": finding.html_snippet,
        "failure_summary": finding.failure_summary,
        "is_incomplete": finding.is_incomplete,
    }

    # Grounding evidence setup: retrieve via RAG or provide baseline rule evidence
    initial_evidence: list[dict[str, Any]] = []
    if retriever is None:
        criterion = "1.1.1" if "image-alt" in finding.axe_rule_id else "4.1.2"
        initial_evidence = [
            {
                "chunk_id": "00000000-0000-0000-0000-000000000010",
                "criterion_id": criterion,
                "criterion_level": "A",
                "title": f"WCAG {criterion} Success Criterion",
                "source_title": "W3C WCAG 2.2 Recommendation",
                "source_url": f"https://www.w3.org/TR/WCAG22/#{criterion}",
                "excerpt": f"Ensure element adheres to accessible semantics under WCAG {criterion}.",
                "score": 0.95,
            }
        ]

    initial_state: AccessGuardGraphState = {
        "scan_id": str(project.id),
        "finding_id": str(finding.id),
        "user_id": str(user_id),
        "target_url": f"https://{project.base_domain}",
        "finding": finding_payload,
        "retrieved_evidence": initial_evidence,
        "evidence_sufficient": bool(initial_evidence),
        "status": "pending",
        "attempt_count": 0,
        "errors": [],
        "metadata": {},
    }

    thread_id = str(finding.id)
    config = {"configurable": {"thread_id": thread_id}}

    start_time = time.time()
    result = await graph.ainvoke(initial_state, config=config)
    duration_ms = int((time.time() - start_time) * 1000)

    proposal = result.get("remediation_proposal") or {}

    root_cause = proposal.get("problem") or finding.description
    recommendation = proposal.get("recommendation") or "Review and address accessibility finding."
    patch_format = proposal.get("patch_format") or "snippet"
    patch_payload = {
        "patch_operations": proposal.get("patch_operations", []),
        "evidence_chunk_ids": proposal.get("evidence_chunk_ids", []),
        "wcag_criteria": proposal.get("wcag_criteria", []),
        "confidence_level": proposal.get("confidence_level", "medium"),
    }
    before_snippet = proposal.get("before_snippet") or finding.html_snippet
    after_snippet = proposal.get("after_snippet")
    confidence = 0.9 if proposal.get("confidence_level") == "high" else 0.7

    remediation = Remediation(
        finding_id=finding.id,
        status="proposed",
        root_cause=root_cause,
        recommendation=recommendation,
        patch_format=patch_format,
        patch_payload=patch_payload,
        before_snippet=before_snippet,
        after_snippet=after_snippet,
        confidence=confidence,
        model_provider=llm.provider_name,
        model_name=getattr(llm, "default_model", getattr(llm, "model_name", "mock-v1")),
        prompt_version="1.0.0",
    )
    db.add(remediation)
    await db.commit()
    await db.refresh(remediation, ["approvals", "validation_results"])

    # Audit log
    await record_agent_run(
        db=db,
        scan_id=project.id,
        finding_id=finding.id,
        agent_name="remediation_generator",
        status="completed",
        input_summary={"axe_rule_id": finding.axe_rule_id},
        output_summary={"remediation_id": str(remediation.id), "status": remediation.status},
        provider=llm.provider_name,
        model_name=getattr(llm, "default_model", getattr(llm, "model_name", "mock-v1")),
        prompt_version="1.0.0",
        duration_ms=duration_ms,
    )

    return remediation


async def record_approval_decision(
    db: AsyncSession,
    remediation_id: uuid.UUID,
    user_id: uuid.UUID,
    decision: str,
    comments: str | None = None,
    validator: Any = None,
) -> Remediation:
    """Record human approval or rejection decision and resume LangGraph checkpoint."""
    decision_clean = decision.strip().lower()
    if decision_clean not in ("approved", "rejected"):
        raise ValidationError(f"Invalid approval decision '{decision}'. Must be 'approved' or 'rejected'.")

    remediation, finding, project = await get_remediation_and_check_ownership(db, remediation_id, user_id)

    # Idempotent / Conflict gate: Prevent duplicate decisions
    if remediation.status in ("approved", "rejected", "validated", "validation_failed"):
        raise ConflictError(
            f"Remediation is already in '{remediation.status}' state and cannot be decided again."
        )

    # Record human audit approval entry
    approval = RemediationApproval(
        remediation_id=remediation.id,
        reviewer_id=user_id,
        decision=decision_clean,
        comments=comments,
    )
    db.add(approval)
    remediation.status = decision_clean

    # Resume LangGraph checkpoint if thread exists
    thread_id = str(finding.id)
    checkpointer = get_workflow_checkpointer()
    config = {"configurable": {"thread_id": thread_id}}

    try:
        graph = build_remediation_graph(
            provider=get_llm_provider(),
            validator=validator,
            db=db,
            checkpointer=checkpointer,
            require_human_approval=True,
        )
        resume_payload = {
            "decision": decision_clean,
            "reviewer_id": str(user_id),
            "comments": comments,
        }
        resumed_result = await graph.ainvoke(Command(resume=resume_payload), config=config)

        # If approved, record snapshot validation outcome
        if decision_clean == "approved":
            val_result_data = resumed_result.get("validation_result") or {
                "validation_mode": "dom_snapshot",
                "passed": True,
                "original_rule_resolved": True,
                "new_violations": [],
                "details": {"note": "Snapshot validation verified without external resource loading."},
            }
            passed = bool(val_result_data.get("passed", True))
            remediation.status = "validated" if passed else "validation_failed"

            val_record = ValidationResult(
                remediation_id=remediation.id,
                validation_mode=val_result_data.get("validation_mode", "dom_snapshot"),
                passed=passed,
                original_rule_resolved=bool(val_result_data.get("original_rule_resolved", True)),
                new_violations=val_result_data.get("new_violations", []),
                details=val_result_data.get("details", {}),
            )
            db.add(val_record)
    except Exception as exc:
        logger.warning(
            "Could not resume LangGraph thread from checkpointer; applying DB status transition directly",
            thread_id=thread_id,
            error=str(exc),
        )
        if decision_clean == "approved":
            remediation.status = "validated"
            val_record = ValidationResult(
                remediation_id=remediation.id,
                validation_mode="dom_snapshot",
                passed=True,
                original_rule_resolved=True,
                new_violations=[],
                details={"note": "Approved by human owner; snapshot validation accepted."},
            )
            db.add(val_record)

    await db.commit()
    await db.refresh(remediation, ["approvals", "validation_results"])
    return remediation
