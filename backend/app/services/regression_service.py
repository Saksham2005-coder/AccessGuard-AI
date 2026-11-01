"""Regression Monitoring and Historical Accessibility Analysis Service.

Phase 19 Feature 6: Stable versioned finding fingerprints, coverage-aware comparison,
pinned baselines, scheduled audits, and in-app notifications.
"""

import hashlib
import logging
import re
import urllib.parse
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError, PolicyViolationError
from app.db.models.finding import Finding
from app.db.models.project import Project
from app.db.models.regression import InAppNotification, ProjectBaseline, ScanSchedule
from app.db.models.scan import Scan
from app.db.models.scan_page import ScanPage
from app.schemas.regression import (
    CoverageSummary,
    InAppNotificationResponse,
    ProjectBaselineResponse,
    RegressionComparisonReport,
    RegressionComparisonSummary,
    RegressionFindingItem,
    ScanScheduleCreate,
    ScanScheduleResponse,
)
from app.services.project_service import get_project_verification_status
from app.services.scan_persistence_service import get_scan

logger = logging.getLogger(__name__)


def normalize_url(url: str) -> str:
    """Normalize page URL to canonical format stripping tracking params and fragments."""
    try:
        parsed = urllib.parse.urlparse(url.strip())
        scheme = parsed.scheme.lower() or "https"
        netloc = parsed.netloc.lower()

        # Remove default ports
        if netloc.endswith(":80"):
            netloc = netloc[:-3]
        elif netloc.endswith(":443"):
            netloc = netloc[:-4]

        # Strip tracking query params
        query_params = urllib.parse.parse_qsl(parsed.query)
        cleaned_params = [
            (k, v)
            for k, v in query_params
            if not k.lower().startswith(("utm_", "fbclid", "gclid", "_ga"))
        ]
        query = urllib.parse.urlencode(sorted(cleaned_params))

        # Normalize path
        path = parsed.path or "/"
        if path != "/" and path.endswith("/"):
            path = path[:-1]

        return urllib.parse.urlunparse((scheme, netloc, path, "", query, ""))
    except Exception:
        return url.strip().lower()


def compute_finding_fingerprint(
    canonical_url: str,
    axe_rule_id: str,
    selector: str | None,
    html_snippet: str | None,
    impact: str | None,
) -> str:
    """Compute deterministic v1 fingerprint for an accessibility finding."""
    norm_selector = re.sub(r"\s+", " ", (selector or "").strip())
    norm_snippet = re.sub(r"\s+", " ", (html_snippet or "").strip().lower())
    norm_impact = (impact or "moderate").strip().lower()

    raw_payload = f"{canonical_url}|{axe_rule_id.strip()}|{norm_selector}|{norm_snippet}|{norm_impact}"
    hash_digest = hashlib.sha256(raw_payload.encode("utf-8")).hexdigest()
    return f"v1:{hash_digest[:24]}"


async def compare_scans(
    db: AsyncSession,
    *,
    project_id: uuid.UUID,
    current_scan_id: uuid.UUID,
    baseline_scan_id: uuid.UUID,
    user_id: uuid.UUID,
    baseline_type: str = "custom_selection",
) -> RegressionComparisonReport:
    """Execute evidence-backed, coverage-aware regression comparison between two scans."""
    # 1. Authorize scans
    current_scan = await get_scan(db, current_scan_id, user_id)
    baseline_scan = await get_scan(db, baseline_scan_id, user_id)

    if current_scan.project_id != project_id or baseline_scan.project_id != project_id:
        raise NotFoundError("One or both scans do not belong to the specified project.")

    # 2. Load pages for both scans
    curr_pages_res = await db.execute(select(ScanPage).where(ScanPage.scan_id == current_scan.id))
    current_pages = list(curr_pages_res.scalars().all())

    base_pages_res = await db.execute(select(ScanPage).where(ScanPage.scan_id == baseline_scan.id))
    baseline_pages = list(base_pages_res.scalars().all())

    curr_pages_map: dict[str, ScanPage] = {normalize_url(p.url): p for p in current_pages}
    base_pages_map: dict[str, ScanPage] = {normalize_url(p.url): p for p in baseline_pages}

    matched_urls = set(base_pages_map.keys()) & set(curr_pages_map.keys())
    missing_urls = set(base_pages_map.keys()) - set(curr_pages_map.keys())
    new_urls = set(curr_pages_map.keys()) - set(base_pages_map.keys())

    coverage_notes: list[str] = []
    coverage_status = "full"
    if missing_urls:
        coverage_status = "partial"
        coverage_notes.append(
            f"Coverage reduction detected: {len(missing_urls)} page(s) present in baseline were not audited in current scan."
        )
    if new_urls:
        coverage_notes.append(
            f"Coverage expansion: {len(new_urls)} new page(s) were audited in current scan."
        )

    coverage_summary = CoverageSummary(
        baseline_pages_count=len(base_pages_map),
        current_pages_count=len(curr_pages_map),
        matched_pages_count=len(matched_urls),
        missing_pages_count=len(missing_urls),
        new_pages_count=len(new_urls),
        coverage_status=coverage_status,
        notes=coverage_notes,
    )

    # 3. Load all findings for both scans
    curr_findings_res = await db.execute(
        select(Finding, ScanPage.url)
        .join(ScanPage, Finding.scan_page_id == ScanPage.id)
        .where(ScanPage.scan_id == current_scan.id)
    )
    current_findings_data = list(curr_findings_res.all())

    base_findings_res = await db.execute(
        select(Finding, ScanPage.url)
        .join(ScanPage, Finding.scan_page_id == ScanPage.id)
        .where(ScanPage.scan_id == baseline_scan.id)
    )
    baseline_findings_data = list(base_findings_res.all())

    # Index baseline findings
    # baseline_by_fingerprint: fingerprint -> (Finding, canonical_url)
    base_by_fp: dict[str, tuple[Finding, str]] = {}
    # baseline_by_location: (canonical_url, axe_rule_id, normalized_selector) -> (Finding, canonical_url)
    base_by_loc: dict[tuple[str, str, str], tuple[Finding, str]] = {}
    accounted_baseline_finding_ids: set[uuid.UUID] = set()

    for f, raw_url in baseline_findings_data:
        c_url = normalize_url(raw_url)
        fp = compute_finding_fingerprint(c_url, f.axe_rule_id, f.selector, f.html_snippet, f.impact)
        base_by_fp[fp] = (f, c_url)
        loc_key = (c_url, f.axe_rule_id, re.sub(r"\s+", " ", (f.selector or "").strip()))
        base_by_loc[loc_key] = (f, c_url)

    result_findings: list[RegressionFindingItem] = []

    # 4. Classify current findings
    for curr_f, raw_url in current_findings_data:
        c_url = normalize_url(raw_url)
        fp = compute_finding_fingerprint(c_url, curr_f.axe_rule_id, curr_f.selector, curr_f.html_snippet, curr_f.impact)
        loc_key = (c_url, curr_f.axe_rule_id, re.sub(r"\s+", " ", (curr_f.selector or "").strip()))

        if fp in base_by_fp:
            # Exact persistent match
            matched_base_f, _ = base_by_fp[fp]
            accounted_baseline_finding_ids.add(matched_base_f.id)
            result_findings.append(
                RegressionFindingItem(
                    finding_id=str(curr_f.id),
                    page_url=raw_url,
                    axe_rule_id=curr_f.axe_rule_id,
                    impact=curr_f.impact,
                    description=curr_f.description,
                    selector=curr_f.selector,
                    html_snippet=curr_f.html_snippet,
                    wcag_tags=curr_f.wcag_tags or [],
                    classification="persistent",
                    change_details="Unchanged across audits",
                    fingerprint=fp,
                )
            )
        elif loc_key in base_by_loc:
            # Same rule and selector, but impact or snippet changed
            matched_base_f, _ = base_by_loc[loc_key]
            accounted_baseline_finding_ids.add(matched_base_f.id)
            change_notes: list[str] = []
            if matched_base_f.impact != curr_f.impact:
                change_notes.append(f"Impact shifted from {matched_base_f.impact} to {curr_f.impact}")
            else:
                change_notes.append("HTML structure or context changed")

            result_findings.append(
                RegressionFindingItem(
                    finding_id=str(curr_f.id),
                    page_url=raw_url,
                    axe_rule_id=curr_f.axe_rule_id,
                    impact=curr_f.impact,
                    description=curr_f.description,
                    selector=curr_f.selector,
                    html_snippet=curr_f.html_snippet,
                    wcag_tags=curr_f.wcag_tags or [],
                    classification="changed",
                    change_details="; ".join(change_notes),
                    fingerprint=fp,
                )
            )
        else:
            # Newly introduced finding
            result_findings.append(
                RegressionFindingItem(
                    finding_id=str(curr_f.id),
                    page_url=raw_url,
                    axe_rule_id=curr_f.axe_rule_id,
                    impact=curr_f.impact,
                    description=curr_f.description,
                    selector=curr_f.selector,
                    html_snippet=curr_f.html_snippet,
                    wcag_tags=curr_f.wcag_tags or [],
                    classification="new",
                    change_details="Introduced since baseline scan",
                    fingerprint=fp,
                )
            )

    # 5. Classify baseline findings not accounted for in current scan
    for base_f, raw_url in baseline_findings_data:
        if base_f.id in accounted_baseline_finding_ids:
            continue

        c_url = normalize_url(raw_url)
        fp = compute_finding_fingerprint(c_url, base_f.axe_rule_id, base_f.selector, base_f.html_snippet, base_f.impact)

        if c_url in missing_urls:
            # Page was NOT scanned in current audit -> inconclusive, NOT resolved!
            result_findings.append(
                RegressionFindingItem(
                    finding_id=str(base_f.id),
                    page_url=raw_url,
                    axe_rule_id=base_f.axe_rule_id,
                    impact=base_f.impact,
                    description=base_f.description,
                    selector=base_f.selector,
                    html_snippet=base_f.html_snippet,
                    wcag_tags=base_f.wcag_tags or [],
                    classification="inconclusive",
                    change_details="Page was not audited in current scan; cannot confirm resolution",
                    fingerprint=fp,
                )
            )
        else:
            # Page was scanned and finding is genuinely absent -> resolved!
            result_findings.append(
                RegressionFindingItem(
                    finding_id=str(base_f.id),
                    page_url=raw_url,
                    axe_rule_id=base_f.axe_rule_id,
                    impact=base_f.impact,
                    description=base_f.description,
                    selector=base_f.selector,
                    html_snippet=base_f.html_snippet,
                    wcag_tags=base_f.wcag_tags or [],
                    classification="resolved",
                    change_details="Resolved in current audit",
                    fingerprint=fp,
                )
            )

    # 6. Compute summary
    new_count = sum(1 for f in result_findings if f.classification == "new")
    resolved_count = sum(1 for f in result_findings if f.classification == "resolved")
    persistent_count = sum(1 for f in result_findings if f.classification == "persistent")
    changed_count = sum(1 for f in result_findings if f.classification == "changed")
    inconclusive_count = sum(1 for f in result_findings if f.classification == "inconclusive")
    has_critical_regression = any(
        f.classification == "new" and f.impact == "critical" for f in result_findings
    )

    summary = RegressionComparisonSummary(
        new_count=new_count,
        resolved_count=resolved_count,
        persistent_count=persistent_count,
        changed_count=changed_count,
        inconclusive_count=inconclusive_count,
        net_change=new_count - resolved_count,
        has_critical_regression=has_critical_regression,
    )

    return RegressionComparisonReport(
        project_id=str(project_id),
        current_scan_id=str(current_scan.id),
        baseline_scan_id=str(baseline_scan.id),
        baseline_type=baseline_type,
        current_scan_date=(current_scan.completed_at or current_scan.created_at or datetime.now(UTC)).isoformat(),
        baseline_scan_date=(baseline_scan.completed_at or baseline_scan.created_at or datetime.now(UTC)).isoformat(),
        coverage=coverage_summary,
        summary=summary,
        findings=result_findings,
        fingerprint_version="v1",
        compared_at=datetime.now(UTC).isoformat(),
    )


# Baseline Management
async def get_or_determine_baseline(
    db: AsyncSession,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    reference_scan_id: uuid.UUID | None = None,
) -> tuple[Scan, str]:
    """Retrieve pinned baseline or fallback to previous completed scan."""
    # 1. Check for user-pinned baseline
    pinned_res = await db.execute(
        select(ProjectBaseline).where(ProjectBaseline.project_id == project_id)
    )
    pinned = pinned_res.scalar_one_or_none()
    if pinned:
        baseline_scan = await get_scan(db, pinned.scan_id, user_id)
        return baseline_scan, "pinned"

    # 2. Fallback to latest previous completed scan
    query = select(Scan).where(
        Scan.project_id == project_id,
        Scan.status == "completed",
    )
    if reference_scan_id:
        query = query.where(Scan.id != reference_scan_id)
    query = query.order_by(desc(Scan.created_at)).limit(1)

    result = await db.execute(query)
    fallback = result.scalar_one_or_none()
    if fallback:
        return fallback, "previous_successful"

    raise NotFoundError("No comparable baseline scan available for this project.")


async def set_project_baseline(
    db: AsyncSession,
    project_id: uuid.UUID,
    scan_id: uuid.UUID,
    user_id: uuid.UUID,
    notes: str | None = None,
) -> ProjectBaselineResponse:
    """Designate and pin a completed scan as project baseline."""
    scan = await get_scan(db, scan_id, user_id)
    if scan.project_id != project_id:
        raise NotFoundError("Scan does not belong to the project.")
    if scan.status != "completed":
        raise PolicyViolationError("Only successfully completed scans may be designated as a baseline.")

    existing_res = await db.execute(
        select(ProjectBaseline).where(ProjectBaseline.project_id == project_id)
    )
    existing = existing_res.scalar_one_or_none()

    if existing:
        existing.scan_id = scan.id
        existing.pinned_by = user_id
        existing.notes = notes
        record = existing
    else:
        record = ProjectBaseline(
            project_id=project_id,
            scan_id=scan.id,
            pinned_by=user_id,
            notes=notes,
        )
        db.add(record)

    await db.commit()
    await db.refresh(record)

    return ProjectBaselineResponse(
        id=str(record.id),
        project_id=str(record.project_id),
        scan_id=str(record.scan_id),
        scan_date=(scan.completed_at or scan.created_at).isoformat(),
        scan_target_url=scan.target_url,
        pinned_at=record.created_at.isoformat(),
        notes=record.notes,
    )


async def get_project_baseline_info(
    db: AsyncSession,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
) -> ProjectBaselineResponse | None:
    """Get project pinned baseline information if set."""
    pinned_res = await db.execute(
        select(ProjectBaseline).where(ProjectBaseline.project_id == project_id)
    )
    pinned = pinned_res.scalar_one_or_none()
    if not pinned:
        return None

    scan = await get_scan(db, pinned.scan_id, user_id)
    return ProjectBaselineResponse(
        id=str(pinned.id),
        project_id=str(pinned.project_id),
        scan_id=str(pinned.scan_id),
        scan_date=(scan.completed_at or scan.created_at).isoformat(),
        scan_target_url=scan.target_url,
        pinned_at=pinned.created_at.isoformat(),
        notes=pinned.notes,
    )


# Scan Scheduling
def calculate_next_run(cadence: str) -> datetime:
    """Calculate next UTC run timestamp based on cadence."""
    now = datetime.now(UTC)
    c = cadence.lower().strip()
    if c == "daily":
        return now + timedelta(days=1)
    if c == "biweekly":
        return now + timedelta(days=14)
    if c == "monthly":
        return now + timedelta(days=30)
    # Default weekly
    return now + timedelta(days=7)


async def create_scan_schedule(
    db: AsyncSession,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    data: ScanScheduleCreate,
) -> ScanScheduleResponse:
    """Create a recurring scheduled accessibility scan with domain verification check."""
    # Enforce domain verification requirement
    is_verified = await get_project_verification_status(db, project_id)
    if not is_verified:
        raise PolicyViolationError(
            "Domain verification is mandatory before enabling automated scheduled audits."
        )

    # Verify project exists and belongs to user
    proj_res = await db.execute(
        select(Project).where(Project.id == project_id, Project.owner_id == user_id)
    )
    project = proj_res.scalar_one_or_none()
    if not project:
        raise NotFoundError("Project not found.")

    schedule = ScanSchedule(
        project_id=project_id,
        owner_id=user_id,
        cadence=data.cadence.lower(),
        target_url=data.target_url.strip(),
        is_active=True,
        next_run_at=calculate_next_run(data.cadence),
        notify_on_regression=data.notify_on_regression,
    )
    db.add(schedule)
    await db.commit()
    await db.refresh(schedule)

    return ScanScheduleResponse(
        id=str(schedule.id),
        project_id=str(schedule.project_id),
        cadence=schedule.cadence,
        target_url=schedule.target_url,
        is_active=schedule.is_active,
        last_run_at=schedule.last_run_at.isoformat() if schedule.last_run_at else None,
        next_run_at=schedule.next_run_at.isoformat() if schedule.next_run_at else None,
        notify_on_regression=schedule.notify_on_regression,
        created_at=schedule.created_at.isoformat(),
    )


async def list_project_schedules(
    db: AsyncSession,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
) -> list[ScanScheduleResponse]:
    """List recurring schedules for an authorized project."""
    res = await db.execute(
        select(ScanSchedule)
        .where(ScanSchedule.project_id == project_id, ScanSchedule.owner_id == user_id)
        .order_by(desc(ScanSchedule.created_at))
    )
    schedules = list(res.scalars().all())
    return [
        ScanScheduleResponse(
            id=str(s.id),
            project_id=str(s.project_id),
            cadence=s.cadence,
            target_url=s.target_url,
            is_active=s.is_active,
            last_run_at=s.last_run_at.isoformat() if s.last_run_at else None,
            next_run_at=s.next_run_at.isoformat() if s.next_run_at else None,
            notify_on_regression=s.notify_on_regression,
            created_at=s.created_at.isoformat(),
        )
        for s in schedules
    ]


async def toggle_scan_schedule(
    db: AsyncSession,
    project_id: uuid.UUID,
    schedule_id: uuid.UUID,
    user_id: uuid.UUID,
    is_active: bool,
) -> ScanScheduleResponse:
    """Pause or resume a scan schedule."""
    res = await db.execute(
        select(ScanSchedule).where(
            ScanSchedule.id == schedule_id,
            ScanSchedule.project_id == project_id,
            ScanSchedule.owner_id == user_id,
        )
    )
    schedule = res.scalar_one_or_none()
    if not schedule:
        raise NotFoundError("Schedule not found.")

    schedule.is_active = is_active
    if is_active:
        schedule.next_run_at = calculate_next_run(schedule.cadence)

    await db.commit()
    await db.refresh(schedule)

    return ScanScheduleResponse(
        id=str(schedule.id),
        project_id=str(schedule.project_id),
        cadence=schedule.cadence,
        target_url=schedule.target_url,
        is_active=schedule.is_active,
        last_run_at=schedule.last_run_at.isoformat() if schedule.last_run_at else None,
        next_run_at=schedule.next_run_at.isoformat() if schedule.next_run_at else None,
        notify_on_regression=schedule.notify_on_regression,
        created_at=schedule.created_at.isoformat(),
    )


async def delete_scan_schedule(
    db: AsyncSession,
    project_id: uuid.UUID,
    schedule_id: uuid.UUID,
    user_id: uuid.UUID,
) -> None:
    """Delete a scan schedule permanently."""
    res = await db.execute(
        select(ScanSchedule).where(
            ScanSchedule.id == schedule_id,
            ScanSchedule.project_id == project_id,
            ScanSchedule.owner_id == user_id,
        )
    )
    schedule = res.scalar_one_or_none()
    if not schedule:
        raise NotFoundError("Schedule not found.")

    await db.delete(schedule)
    await db.commit()


# In-App Notifications
async def create_in_app_notification(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    project_id: uuid.UUID | None = None,
    title: str,
    message: str,
    notification_type: str = "regression_detected",
    link_url: str | None = None,
) -> InAppNotification:
    """Create in-app notification record for accessibility regression or alert."""
    notification = InAppNotification(
        user_id=user_id,
        project_id=project_id,
        title=title,
        message=message,
        notification_type=notification_type,
        link_url=link_url,
        is_read=False,
    )
    db.add(notification)
    await db.commit()
    await db.refresh(notification)
    return notification


async def list_user_notifications(
    db: AsyncSession,
    user_id: uuid.UUID,
    unread_only: bool = False,
) -> list[InAppNotificationResponse]:
    """Retrieve notifications for authenticated user."""
    query = select(InAppNotification).where(InAppNotification.user_id == user_id)
    if unread_only:
        query = query.where(InAppNotification.is_read.is_(False))
    query = query.order_by(desc(InAppNotification.created_at)).limit(50)

    res = await db.execute(query)
    notifications = list(res.scalars().all())

    return [
        InAppNotificationResponse(
            id=str(n.id),
            title=n.title,
            message=n.message,
            notification_type=n.notification_type,
            link_url=n.link_url,
            is_read=n.is_read,
            created_at=n.created_at.isoformat(),
        )
        for n in notifications
    ]


async def mark_notification_read(
    db: AsyncSession,
    notification_id: uuid.UUID,
    user_id: uuid.UUID,
) -> None:
    """Mark notification as read."""
    res = await db.execute(
        select(InAppNotification).where(
            InAppNotification.id == notification_id,
            InAppNotification.user_id == user_id,
        )
    )
    notification = res.scalar_one_or_none()
    if notification:
        notification.is_read = True
        await db.commit()
