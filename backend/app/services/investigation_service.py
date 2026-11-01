"""Service layer managing autonomous accessibility multi-agent investigations."""

import time
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.specialists.coordinator import InvestigationCoordinator
from app.core.errors import NotFoundError
from app.core.logging import get_logger
from app.db.models.agent_run import AgentRun
from app.schemas.investigation import (
    InvestigationReport,
    InvestigationRunSummary,
)
from app.services.scan_persistence_service import get_scan, get_scan_findings

logger = get_logger("investigation_service")


async def run_scan_investigation(
    db: AsyncSession,
    *,
    scan_id: uuid.UUID,
    user_id: uuid.UUID,
    keyboard_run: dict | None = None,
) -> InvestigationReport:
    """Execute multi-specialist investigation for an authorized scan and persist audit record."""
    scan = await get_scan(db, scan_id=scan_id, user_id=user_id)
    findings = await get_scan_findings(db, scan_id=scan.id, user_id=user_id, include_incomplete=True)


    investigation_id = str(uuid.uuid4())
    coordinator = InvestigationCoordinator()

    start_time = time.monotonic()
    report = await coordinator.run_investigation(
        scan=scan,
        findings=findings,
        keyboard_run=keyboard_run,
        investigation_id=investigation_id,
    )
    duration_ms = int((time.monotonic() - start_time) * 1000)
    report.duration_ms = duration_ms

    # Persist in agent_runs table
    agent_run = AgentRun(
        id=uuid.UUID(investigation_id),
        scan_id=scan.id,
        finding_id=None,
        agent_name="autonomous_investigation",
        status=report.status,
        input_summary={
            "scan_id": str(scan.id),
            "target_url": scan.target_url,
            "findings_count": len(findings),
        },
        output_summary=report.model_dump(),
        provider="autonomous_agents",
        model_name="multi_specialist_v1",
        duration_ms=duration_ms,
    )

    db.add(agent_run)
    await db.commit()
    await db.refresh(agent_run)

    logger.info(
        "Completed and persisted autonomous accessibility investigation",
        scan_id=str(scan.id),
        investigation_id=investigation_id,
        findings_count=len(findings),
        status=report.status,
        duration_ms=duration_ms,
    )

    return report


async def get_latest_scan_investigation(
    db: AsyncSession,
    *,
    scan_id: uuid.UUID,
    user_id: uuid.UUID,
) -> InvestigationReport | None:
    """Retrieve the most recent autonomous investigation report for an authorized scan."""
    scan = await get_scan(db, scan_id, user_id)

    query = (
        select(AgentRun)
        .where(
            AgentRun.scan_id == scan.id,
            AgentRun.agent_name == "autonomous_investigation",
        )
        .order_by(AgentRun.created_at.desc())
        .limit(1)
    )
    result = await db.execute(query)
    record = result.scalars().first()
    if not record:
        return None

    report_data = dict(record.output_summary)
    report_data["investigation_id"] = str(record.id)
    report_data["created_at"] = record.created_at.isoformat()
    report_data["duration_ms"] = record.duration_ms
    return InvestigationReport.model_validate(report_data)


async def get_investigation_by_id(
    db: AsyncSession,
    *,
    scan_id: uuid.UUID,
    investigation_id: uuid.UUID,
    user_id: uuid.UUID,
) -> InvestigationReport:
    """Retrieve a specific autonomous investigation report by ID with tenant validation."""
    scan = await get_scan(db, scan_id, user_id)

    query = select(AgentRun).where(
        AgentRun.id == investigation_id,
        AgentRun.scan_id == scan.id,
        AgentRun.agent_name == "autonomous_investigation",
    )
    result = await db.execute(query)
    record = result.scalars().first()
    if not record:
        raise NotFoundError("Investigation record not found")

    report_data = dict(record.output_summary)
    report_data["investigation_id"] = str(record.id)
    report_data["created_at"] = record.created_at.isoformat()
    report_data["duration_ms"] = record.duration_ms
    return InvestigationReport.model_validate(report_data)


async def list_scan_investigations(
    db: AsyncSession,
    *,
    scan_id: uuid.UUID,
    user_id: uuid.UUID,
) -> list[InvestigationRunSummary]:
    """List historical autonomous investigations conducted for a scan."""
    scan = await get_scan(db, scan_id, user_id)

    query = (
        select(AgentRun)
        .where(
            AgentRun.scan_id == scan.id,
            AgentRun.agent_name == "autonomous_investigation",
        )
        .order_by(AgentRun.created_at.desc())
    )
    result = await db.execute(query)
    records = result.scalars().all()

    items: list[InvestigationRunSummary] = []
    for r in records:
        out = r.output_summary or {}
        items.append(
            InvestigationRunSummary(
                id=str(r.id),
                scan_id=str(scan.id),
                status=r.status,
                overall_confidence=out.get("overall_confidence", "tentative"),
                executive_summary=out.get("executive_summary", "Autonomous investigation record"),
                created_at=r.created_at.isoformat(),
            )
        )

    return items
