"""Scan, page, and accessibility finding persistence service with tenant isolation."""

import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import ConflictError, NotFoundError
from app.core.logging import get_logger
from app.db.base import utc_now
from app.db.models.finding import Finding, FindingNode
from app.db.models.project import Project
from app.db.models.scan import Scan
from app.db.models.scan_page import ScanPage
from app.db.models.user import User
from app.scanner.axe_runner import AxeAuditResult

logger = get_logger("scan_persistence")


async def create_scan_record(
    db: AsyncSession,
    project: Project,
    user: User,
    target_url: str,
    scan_config: dict[str, Any] | None = None,
    axe_version: str | None = None,
    browser_version: str | None = None,
) -> Scan:
    """Create and persist a new Scan entity for an authorized, verified project."""
    if project.owner_id != user.id:
        raise NotFoundError("Project not found.")

    effective_config = scan_config or {}

    scan = Scan(
        project_id=project.id,
        requested_by=user.id,
        target_url=target_url,
        status="pending",
        config=effective_config,
        axe_version=axe_version,
        browser_version=browser_version,
    )
    db.add(scan)
    await db.flush()
    await db.refresh(scan)

    logger.info(
        "Created scan job record",
        scan_id=str(scan.id),
        project_id=str(project.id),
        target_url=target_url,
    )
    return scan


async def persist_page_audit_results(
    db: AsyncSession,
    scan_id: uuid.UUID,
    url: str,
    normalized_url: str,
    audit_result: AxeAuditResult,
    page_title: str | None = None,
    http_status: int | None = 200,
    load_duration_ms: int | None = None,
    audit_status: str = "completed",
    error_code: str | None = None,
    error_summary: str | None = None,
    screenshot_storage_key: str | None = None,
    viewport_width: int | None = 1280,
    viewport_height: int | None = 800,
    device_pixel_ratio: float | None = 1.0,
    element_geometries: dict[str, Any] | None = None,
) -> ScanPage:
    """Persist a crawled page along with its normalized axe-core violations, incomplete findings, and DOM geometry."""
    # Check duplicate normalized_url for this scan to enforce idempotency
    existing_page = await db.execute(
        select(ScanPage).where(
            ScanPage.scan_id == scan_id,
            ScanPage.normalized_url == normalized_url,
        )
    )
    if existing_page.scalar_one_or_none() is not None:
        raise ConflictError(
            f"Page '{normalized_url}' has already been recorded for scan {scan_id}."
        )

    now = utc_now()
    scan_page = ScanPage(
        scan_id=scan_id,
        url=url,
        normalized_url=normalized_url,
        page_title=page_title,
        http_status=http_status,
        audit_status=audit_status,
        load_duration_ms=load_duration_ms,
        screenshot_storage_key=screenshot_storage_key,
        viewport_width=viewport_width,
        viewport_height=viewport_height,
        device_pixel_ratio=device_pixel_ratio,
        error_code=error_code,
        error_summary=error_summary,
        scanned_at=now,
    )
    db.add(scan_page)
    await db.flush()
    await db.refresh(scan_page)

    # Persist violations
    total_violations_added = 0
    all_findings_to_store = []
    for item in audit_result.violations:
        all_findings_to_store.append((item, False))
    for item in audit_result.incomplete:
        all_findings_to_store.append((item, True))

    geoms = element_geometries or {}

    for finding_item, is_incomplete in all_findings_to_store:
        primary_sel = finding_item.primary_selector
        geom_info = geoms.get(primary_sel)
        finding_bbox = None
        finding_geom_status = "not_located"

        if geom_info:
            if hasattr(geom_info, "bounding_box") and geom_info.bounding_box:
                finding_bbox = geom_info.bounding_box.model_dump()
            elif isinstance(geom_info, dict) and geom_info.get("bounding_box"):
                finding_bbox = geom_info["bounding_box"]

            if hasattr(geom_info, "status"):
                finding_geom_status = geom_info.status
            elif isinstance(geom_info, dict):
                finding_geom_status = geom_info.get("status", "not_located")

        finding = Finding(
            scan_page_id=scan_page.id,
            axe_rule_id=finding_item.rule_id,
            impact=finding_item.impact,
            description=finding_item.description,
            help=finding_item.help_text,
            help_url=finding_item.help_url,
            wcag_tags=finding_item.wcag_tags,
            selector=primary_sel,
            html_snippet=(finding_item.nodes[0].html_snippet if finding_item.nodes else None),
            failure_summary=(finding_item.nodes[0].failure_summary if finding_item.nodes else None),
            bounding_box=finding_bbox,
            geometry_status=finding_geom_status,
            fingerprint=finding_item.fingerprint,
            is_incomplete=is_incomplete,
        )
        db.add(finding)
        await db.flush()
        await db.refresh(finding)

        if not is_incomplete:
            total_violations_added += 1

        # Store individual DOM element nodes
        for node in finding_item.nodes:
            node_sel = node.target[0] if node.target else primary_sel
            node_geom = geoms.get(node_sel)
            node_bbox = None
            node_geom_status = "not_located"
            if node_geom:
                if hasattr(node_geom, "bounding_box") and node_geom.bounding_box:
                    node_bbox = node_geom.bounding_box.model_dump()
                elif isinstance(node_geom, dict) and node_geom.get("bounding_box"):
                    node_bbox = node_geom["bounding_box"]

                if hasattr(node_geom, "status"):
                    node_geom_status = node_geom.status
                elif isinstance(node_geom, dict):
                    node_geom_status = node_geom.get("status", "not_located")

            finding_node = FindingNode(
                finding_id=finding.id,
                target=node.target,
                html_snippet=node.html_snippet,
                failure_summary=node.failure_summary,
                bounding_box=node_bbox,
                geometry_status=node_geom_status,
            )
            db.add(finding_node)

    # Update aggregate scan counters
    scan_result = await db.execute(select(Scan).where(Scan.id == scan_id))
    scan = scan_result.scalar_one_or_none()
    if scan:
        scan.total_pages += 1
        if audit_status == "completed":
            scan.pages_succeeded += 1
        else:
            scan.pages_failed += 1
        scan.total_violations += total_violations_added
        await db.flush()

    logger.info(
        "Persisted page audit results",
        scan_id=str(scan_id),
        page_id=str(scan_page.id),
        url=normalized_url,
        violations_stored=total_violations_added,
        incomplete_stored=len(audit_result.incomplete),
    )

    return scan_page


async def get_scan(db: AsyncSession, scan_id: uuid.UUID, user_id: uuid.UUID) -> Scan:
    """Retrieve scan ensuring tenant authorization."""
    result = await db.execute(
        select(Scan)
        .options(selectinload(Scan.pages))
        .where(
            Scan.id == scan_id,
            Scan.requested_by == user_id,
        )
    )
    scan = result.scalar_one_or_none()
    if scan is None:
        raise NotFoundError("Scan not found.")
    return scan


async def get_scan_findings(
    db: AsyncSession,
    scan_id: uuid.UUID,
    user_id: uuid.UUID,
    include_incomplete: bool = False,
) -> list[Finding]:
    """Retrieve all findings for a scan, with optional inclusion of manual-review items."""
    # Ensure tenant authorization
    await get_scan(db, scan_id, user_id)

    query = (
        select(Finding)
        .join(ScanPage, Finding.scan_page_id == ScanPage.id)
        .options(selectinload(Finding.nodes))
        .where(ScanPage.scan_id == scan_id)
    )

    if not include_incomplete:
        query = query.where(Finding.is_incomplete.is_(False))

    result = await db.execute(query.order_by(Finding.created_at.desc()))
    return list(result.scalars().all())
