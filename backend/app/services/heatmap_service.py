"""Visual accessibility heatmap service with density contours, element overlays, and tenant scoping."""

import uuid
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import NotFoundError
from app.db.models.finding import Finding
from app.db.models.project import Project
from app.db.models.scan import Scan
from app.db.models.scan_page import ScanPage
from app.scanner.geometry import (
    HeatmapDensityPoint,
    calculate_density_hotspots,
)
from app.services.storage_service import resolve_artifact_path


class HeatmapMarker(BaseModel):
    """Visual marker representing an accessibility barrier localized to page coordinates."""

    finding_id: str
    rule_id: str
    impact: str | None = None
    selector: str | None = None
    geometry_status: str = Field(
        ...,
        description="Geometry availability: located, not_located, ambiguous, or stale",
    )
    bounding_box: dict[str, float] | None = Field(
        default=None,
        description="Bounding box {x, y, width, height} in CSS document pixels",
    )
    html_snippet: str | None = None
    failure_summary: str | None = None
    wcag_tags: list[str] = Field(default_factory=list)
    is_incomplete: bool = False


class HeatmapViewport(BaseModel):
    """Coordinate space metadata of the rendered page."""

    width: int = 1280
    height: int = 800
    device_pixel_ratio: float = 1.0


class HeatmapResponse(BaseModel):
    """Aggregate payload for the visual accessibility heatmap viewer."""

    scan_id: str
    page_id: str
    url: str
    page_title: str | None = None
    screenshot_url: str | None = None
    viewport: HeatmapViewport
    total_findings: int
    located_findings: int
    ambiguous_findings: int
    unlocated_findings: int
    markers: list[HeatmapMarker]
    density_points: list[HeatmapDensityPoint]


class ScanPageSummary(BaseModel):
    """Summary of a crawled page within an audited scan."""

    id: str
    url: str
    page_title: str | None = None
    http_status: int | None = None
    audit_status: str
    violations_count: int = 0
    has_screenshot: bool = False


async def verify_scan_tenant_access(
    db: AsyncSession,
    scan_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Scan:
    """Verify that scan exists and belongs to a project owned by the user."""
    stmt = (
        select(Scan)
        .join(Project, Scan.project_id == Project.id)
        .where(
            Scan.id == scan_id,
            Project.owner_id == user_id,
        )
    )
    res = await db.execute(stmt)
    scan = res.scalar_one_or_none()
    if not scan:
        raise NotFoundError("Scan not found or access denied")
    return scan


async def get_page_heatmap(
    db: AsyncSession,
    scan_id: uuid.UUID,
    page_id: uuid.UUID,
    user_id: uuid.UUID,
) -> HeatmapResponse:
    """Compile visual heatmap coordinates, density contours, and evidence markers."""
    # Enforce tenant isolation boundary
    await verify_scan_tenant_access(db, scan_id, user_id)

    # Fetch scan page
    page_stmt = (
        select(ScanPage)
        .where(
            ScanPage.id == page_id,
            ScanPage.scan_id == scan_id,
        )
    )
    page_res = await db.execute(page_stmt)
    page = page_res.scalar_one_or_none()
    if not page:
        raise NotFoundError("Scan page not found")

    # Fetch all findings for this page with nodes
    findings_stmt = (
        select(Finding)
        .options(selectinload(Finding.nodes))
        .where(Finding.scan_page_id == page_id)
        .order_by(Finding.created_at.asc())
    )
    findings_res = await db.execute(findings_stmt)
    findings = findings_res.scalars().all()

    markers: list[HeatmapMarker] = []
    marker_dicts_for_density: list[dict[str, Any]] = []

    for f in findings:
        geom_status = f.geometry_status or ("located" if f.bounding_box else "not_located")
        bbox = f.bounding_box

        # Fallback check on individual nodes if primary selector did not have geometry
        if not bbox and f.nodes:
            for n in f.nodes:
                if n.bounding_box:
                    bbox = n.bounding_box
                    geom_status = n.geometry_status or "located"
                    break

        marker = HeatmapMarker(
            finding_id=str(f.id),
            rule_id=f.axe_rule_id,
            impact=f.impact,
            selector=f.selector,
            geometry_status=geom_status,
            bounding_box=bbox,
            html_snippet=f.html_snippet,
            failure_summary=f.failure_summary,
            wcag_tags=f.wcag_tags or [],
            is_incomplete=f.is_incomplete,
        )
        markers.append(marker)

        if bbox:
            marker_dicts_for_density.append({
                "bounding_box": bbox,
                "impact": f.impact,
                "finding_id": str(f.id),
            })

    density_points = calculate_density_hotspots(marker_dicts_for_density)

    # Verify screenshot availability
    screenshot_url: str | None = None
    if page.screenshot_storage_key:
        local_path = resolve_artifact_path(page.screenshot_storage_key)
        if local_path and local_path.is_file():
            screenshot_url = f"/api/v1/scans/{scan_id}/pages/{page_id}/screenshot"

    located_count = sum(1 for m in markers if m.geometry_status == "located")
    ambiguous_count = sum(1 for m in markers if m.geometry_status == "ambiguous")
    unlocated_count = sum(1 for m in markers if m.geometry_status not in ("located", "ambiguous"))

    return HeatmapResponse(
        scan_id=str(scan_id),
        page_id=str(page_id),
        url=page.url,
        page_title=page.page_title,
        screenshot_url=screenshot_url,
        viewport=HeatmapViewport(
            width=page.viewport_width or 1280,
            height=page.viewport_height or 800,
            device_pixel_ratio=page.device_pixel_ratio or 1.0,
        ),
        total_findings=len(markers),
        located_findings=located_count,
        ambiguous_findings=ambiguous_count,
        unlocated_findings=unlocated_count,
        markers=markers,
        density_points=density_points,
    )


async def list_scan_pages(
    db: AsyncSession,
    scan_id: uuid.UUID,
    user_id: uuid.UUID,
) -> list[ScanPageSummary]:
    """List all pages audited within a scan with screenshot indicators and violation counts."""
    await verify_scan_tenant_access(db, scan_id, user_id)

    # Query pages with violation counts
    stmt = (
        select(
            ScanPage,
            func.count(Finding.id).label("findings_count"),
        )
        .outerjoin(Finding, Finding.scan_page_id == ScanPage.id)
        .where(ScanPage.scan_id == scan_id)
        .group_by(ScanPage.id)
        .order_by(ScanPage.created_at.asc())
    )
    res = await db.execute(stmt)
    rows = res.all()

    summaries: list[ScanPageSummary] = []
    for page, count in rows:
        has_ss = False
        if page.screenshot_storage_key:
            p = resolve_artifact_path(page.screenshot_storage_key)
            has_ss = bool(p and p.is_file())

        summaries.append(
            ScanPageSummary(
                id=str(page.id),
                url=page.url,
                page_title=page.page_title,
                http_status=page.http_status,
                audit_status=page.audit_status,
                violations_count=count,
                has_screenshot=has_ss,
            )
        )

    return summaries
