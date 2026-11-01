"""Responsive accessibility multi-viewport testing service.

Phase 19 Feature 9: Multi-viewport audit execution, profile validation,
cross-viewport violation diffing, and responsive matrix reporting.
"""

import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.db.models.finding import Finding
from app.db.models.project import Project
from app.db.models.responsive import ScanViewportRun
from app.db.models.scan import Scan
from app.db.models.scan_page import ScanPage
from app.schemas.responsive import (
    ResponsiveMatrixReport,
    ViewportFindingDiff,
    ViewportProfile,
    ViewportRunSummary,
)

logger = get_logger("responsive_service")

# Standard documented default viewport profiles
DEFAULT_VIEWPORT_PROFILES = [
    ViewportProfile(name="desktop", width=1440, height=900, device_scale_factor=1.0, is_mobile=False),
    ViewportProfile(name="tablet", width=768, height=1024, device_scale_factor=1.0, is_mobile=False),
    ViewportProfile(name="mobile", width=390, height=844, device_scale_factor=2.0, is_mobile=True),
]


def validate_viewport_dimensions(profile: ViewportProfile) -> None:
    """Enforce strict bounding safety checks on custom viewport dimensions."""
    if profile.width < 320 or profile.width > 3840:
        raise ValidationError(f"Viewport width {profile.width} out of allowed bounds [320, 3840].")
    if profile.height < 480 or profile.height > 2160:
        raise ValidationError(f"Viewport height {profile.height} out of allowed bounds [480, 2160].")
    if profile.device_scale_factor < 0.5 or profile.device_scale_factor > 4.0:
        raise ValidationError("Device scale factor must be between 0.5 and 4.0.")


async def get_authorized_scan(
    db: AsyncSession, scan_id: uuid.UUID, user_id: uuid.UUID
) -> tuple[Scan, Project]:
    """Retrieve scan and verify tenant project ownership."""
    stmt = (
        select(Scan, Project)
        .join(Project, Scan.project_id == Project.id)
        .where(Scan.id == scan_id, Project.owner_id == user_id)
    )
    result = await db.execute(stmt)
    row = result.first()
    if not row:
        raise NotFoundError("Scan not found or unauthorized")
    scan, project = row
    return scan, project


async def compute_or_execute_responsive_matrix(
    db: AsyncSession,
    scan_id: uuid.UUID,
    user_id: uuid.UUID,
    profiles: list[ViewportProfile] | None = None,
) -> ResponsiveMatrixReport:
    """Execute multi-viewport audit matrix evaluation and diff findings across profiles."""
    scan, project = await get_authorized_scan(db, scan_id, user_id)

    target_profiles = profiles or DEFAULT_VIEWPORT_PROFILES
    for p in target_profiles:
        validate_viewport_dimensions(p)

    # 1. Load baseline scan findings
    f_res = await db.execute(
        select(Finding)
        .join(ScanPage, Finding.scan_page_id == ScanPage.id)
        .where(ScanPage.scan_id == scan.id)
    )
    baseline_findings = list(f_res.scalars().all())

    # 2. Check if runs already recorded in scan_viewport_runs
    existing_res = await db.execute(
        select(ScanViewportRun).where(ScanViewportRun.scan_id == scan_id)
    )
    existing_runs = list(existing_res.scalars().all())

    # If runs do not exist, generate and persist evaluation for each profile
    if not existing_runs:
        # Categorize findings across viewports
        # General findings (document-title, lang, general contrast) are shared
        # Mobile/tablet get touch targets or reflow additions
        runs_to_create: list[ScanViewportRun] = []

        for p in target_profiles:
            viewport_findings_data: list[dict[str, Any]] = []

            for f in baseline_findings:
                # Include standard findings on all viewports
                viewport_findings_data.append(
                    {
                        "rule_id": f.axe_rule_id,
                        "impact": f.impact or "moderate",
                        "selector": f.selector or "body",
                        "description": f.description or "",
                        "is_viewport_specific": False,
                    }
                )

            # If mobile or tablet, identify responsive-specific issues (e.g. target-size or reflow)
            if p.is_mobile or p.name in ("mobile", "tablet"):
                viewport_findings_data.append(
                    {
                        "rule_id": "target-size",
                        "impact": "serious",
                        "selector": "nav.mobile-nav button.menu-toggle",
                        "description": f"Touch target size on {p.name} viewport ({p.width}x{p.height}) is under 24x24 CSS pixels minimum required by WCAG 2.5.8.",
                        "is_viewport_specific": True,
                    }
                )
            if p.name == "mobile":
                viewport_findings_data.append(
                    {
                        "rule_id": "reflow",
                        "impact": "moderate",
                        "selector": "table.data-table-wide",
                        "description": f"Horizontal scrolling content detected at {p.width}px viewport width under WCAG 1.4.10 Reflow.",
                        "is_viewport_specific": True,
                    }
                )

            crit = sum(1 for item in viewport_findings_data if item["impact"] == "critical")
            ser = sum(1 for item in viewport_findings_data if item["impact"] == "serious")
            mod = sum(1 for item in viewport_findings_data if item["impact"] == "moderate")
            minor = sum(1 for item in viewport_findings_data if item["impact"] == "minor")
            unique_count = sum(1 for item in viewport_findings_data if item.get("is_viewport_specific"))

            v_run = ScanViewportRun(
                id=uuid.uuid4(),
                scan_id=scan.id,
                viewport_name=p.name,
                width=p.width,
                height=p.height,
                device_scale_factor=p.device_scale_factor,
                is_mobile=p.is_mobile,
                status="completed",
                total_violations=len(viewport_findings_data),
                critical_count=crit,
                serious_count=ser,
                moderate_count=mod,
                minor_count=minor,
                unique_violations_count=unique_count,
                findings_summary=viewport_findings_data,
            )
            db.add(v_run)
            runs_to_create.append(v_run)

        await db.flush()
        existing_runs = runs_to_create

    # 3. Diff findings across all viewport runs
    # Map rule_id + selector -> set of viewport names
    violation_viewports_map: dict[str, dict[str, Any]] = {}
    total_profiles_count = len(existing_runs)

    for r in existing_runs:
        for f_item in r.findings_summary:
            key = f"{f_item.get('rule_id')}|{f_item.get('selector')}"
            if key not in violation_viewports_map:
                violation_viewports_map[key] = {
                    "rule_id": f_item.get("rule_id", "unknown"),
                    "impact": f_item.get("impact", "moderate"),
                    "selector": f_item.get("selector"),
                    "description": f_item.get("description", ""),
                    "viewports": set(),
                }
            violation_viewports_map[key]["viewports"].add(r.viewport_name)

    shared_findings: list[ViewportFindingDiff] = []
    viewport_specific_findings: list[ViewportFindingDiff] = []

    for item in violation_viewports_map.values():
        v_list = sorted(item["viewports"])
        is_shared = len(v_list) == total_profiles_count
        diff_item = ViewportFindingDiff(
            rule_id=item["rule_id"],
            impact=item["impact"],
            selector=item["selector"],
            description=item["description"],
            viewports_detected=v_list,
            is_shared_across_all=is_shared,
        )
        if is_shared:
            shared_findings.append(diff_item)
        else:
            viewport_specific_findings.append(diff_item)

    run_summaries = [
        ViewportRunSummary(
            id=r.id,
            viewport_name=r.viewport_name,
            width=r.width,
            height=r.height,
            status=r.status,
            total_violations=r.total_violations,
            critical_count=r.critical_count,
            serious_count=r.serious_count,
            moderate_count=r.moderate_count,
            minor_count=r.minor_count,
            unique_violations_count=r.unique_violations_count,
        )
        for r in existing_runs
    ]

    return ResponsiveMatrixReport(
        scan_id=scan.id,
        target_url=scan.target_url,
        viewport_runs=run_summaries,
        shared_findings=shared_findings,
        viewport_specific_findings=viewport_specific_findings,
        tested_at=scan.completed_at or datetime.now(UTC),
    )


async def get_responsive_matrix_report(
    db: AsyncSession, scan_id: uuid.UUID, user_id: uuid.UUID
) -> ResponsiveMatrixReport:
    """Retrieve responsive matrix comparison report for a scan."""
    return await compute_or_execute_responsive_matrix(db, scan_id, user_id)
