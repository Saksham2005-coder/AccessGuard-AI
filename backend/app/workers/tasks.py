"""Celery tasks and async execution pipeline for background accessibility auditing."""

import asyncio
import urllib.parse
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.core.errors import PolicyViolationError
from app.core.logging import get_logger
from app.db.base import utc_now
from app.db.models.project import Project
from app.db.models.scan import Scan
from app.db.session import get_session_maker
from app.scanner.axe_runner import execute_axe_audit, get_axe_version
from app.scanner.browser import create_isolated_browser_context
from app.scanner.crawler import crawl_website
from app.scanner.schemas import CrawlOptions
from app.scanner.target_policy import validate_target_url
from app.services.project_service import get_project_verification_status
from app.services.scan_event_service import record_scan_event
from app.services.scan_persistence_service import persist_page_audit_results
from app.workers.celery_app import celery_app

logger = get_logger("scan_tasks")

# Global cancellation registry for in-process task cancellation
_active_cancellations: set[str] = set()


def request_scan_cancellation(scan_id: uuid.UUID) -> None:
    """Signal cancellation for an active scan."""
    _active_cancellations.add(str(scan_id))


def is_scan_cancelled(scan_id: uuid.UUID) -> bool:
    """Check if cancellation has been requested for a scan."""
    return str(scan_id) in _active_cancellations


async def execute_scan_pipeline(scan_id: uuid.UUID, db: AsyncSession | None = None) -> None:
    """Execute full async scan pipeline across validating, crawling, and auditing stages."""
    if db is not None:
        await _execute_scan_pipeline_core(scan_id, db)
    else:
        session_maker = get_session_maker()
        async with session_maker() as session:
            await _execute_scan_pipeline_core(scan_id, session)


async def _execute_scan_pipeline_core(scan_id: uuid.UUID, db: AsyncSession) -> None:
    settings = get_settings()

    result = await db.execute(
        select(Scan).options(selectinload(Scan.project)).where(Scan.id == scan_id)
    )
    scan = result.scalar_one_or_none()

    if scan is None:
        logger.error("Scan job not found for execution", scan_id=str(scan_id))
        return

    # Idempotency check: do not re-run terminal scans
    if scan.status in ("completed", "completed_with_errors", "failed", "cancelled"):
        logger.info("Scan is already in terminal state", scan_id=str(scan_id), status=scan.status)
        return

    # Early cancellation check before entering validating stage
    if is_scan_cancelled(scan_id):
        scan.status = "cancelled"
        scan.completed_at = utc_now()
        await record_scan_event(
            db, scan.id, "scan_cancelled", {"message": "Scan cancelled by user"}
        )
        await db.commit()
        return

    project: Project = scan.project

    # --- Stage 1: Validating ---
    scan.status = "running"
    scan.started_at = utc_now()
    await db.commit()

    await record_scan_event(
        db,
        scan.id,
        "stage_changed",
        {"stage": "validating", "message": "Validating domain ownership and target safety policy"},
    )
    await db.commit()

    # Check domain verification
    is_verified, _ = await get_project_verification_status(db, project.id)
    if not is_verified:
        scan.status = "failed"
        scan.error_code = "DOMAIN_NOT_VERIFIED"
        scan.error_summary = (
            f"Project base domain '{project.base_domain}' is not verified. "
            "DNS TXT record verification is required before scanning."
        )
        scan.completed_at = utc_now()
        await record_scan_event(
            db,
            scan.id,
            "scan_failed",
            {"error_code": scan.error_code, "error_summary": scan.error_summary},
        )
        await db.commit()
        return

    # Pre-validate target URL
    allow_loopback = settings.TEST_ALLOW_LOOPBACK
    parsed_target = urllib.parse.urlsplit(scan.target_url)
    allowed_ports = {80, 443}
    if allow_loopback and parsed_target.port:
        allowed_ports.add(parsed_target.port)

    try:
        validated_url = await validate_target_url(
            scan.target_url,
            project.base_domain,
            allow_loopback=allow_loopback,
            allowed_ports=allowed_ports,
        )
    except PolicyViolationError as e:
        scan.status = "failed"
        scan.error_code = e.code
        scan.error_summary = str(e)
        scan.completed_at = utc_now()
        await record_scan_event(
            db,
            scan.id,
            "scan_failed",
            {"error_code": e.code, "error_summary": str(e)},
        )
        await db.commit()
        return

    # --- Stage 2: Crawling ---
    if is_scan_cancelled(scan_id):
        scan.status = "cancelled"
        scan.completed_at = utc_now()
        await record_scan_event(
            db, scan.id, "scan_cancelled", {"message": "Scan cancelled by user"}
        )
        await db.commit()
        return

    await record_scan_event(
        db,
        scan.id,
        "stage_changed",
        {"stage": "crawling", "message": "Discovering and rendering same-origin pages"},
    )
    await db.commit()

    crawl_opts = CrawlOptions(
        max_pages=scan.config.get("max_pages", settings.MAX_SCAN_PAGES),
        max_depth=scan.config.get("max_depth", settings.MAX_CRAWL_DEPTH),
        max_duration_seconds=float(
            scan.config.get("max_duration_seconds", settings.SCAN_TOTAL_TIMEOUT_SECONDS)
        ),
        allow_loopback=allow_loopback,
    )

    cancel_event = asyncio.Event()

    async def _on_page_discovered(page_info: Any) -> None:
        if is_scan_cancelled(scan_id):
            cancel_event.set()
        await record_scan_event(
            db,
            scan.id,
            "page_discovered",
            {"url": page_info.url, "depth": page_info.depth},
        )
        await db.commit()

    crawl_summary = await crawl_website(
        start_url=validated_url,
        base_domain=project.base_domain,
        options=crawl_opts,
        cancel_event=cancel_event,
        on_page_crawled=_on_page_discovered,
    )

    if is_scan_cancelled(scan_id):
        scan.status = "cancelled"
        scan.completed_at = utc_now()
        await record_scan_event(
            db, scan.id, "scan_cancelled", {"message": "Scan cancelled by user"}
        )
        await db.commit()
        return

    # --- Stage 3: Auditing ---
    await record_scan_event(
        db,
        scan.id,
        "stage_changed",
        {
            "stage": "auditing",
            "message": "Evaluating axe-core accessibility rules on crawled pages",
        },
    )
    await db.commit()

    axe_version = get_axe_version()
    scan.axe_version = axe_version
    await db.commit()

    # Audit each crawled page
    async with create_isolated_browser_context(allow_loopback=allow_loopback) as context:
        browser_page = await context.new_page()

        for crawled_page in crawl_summary.pages:
            if is_scan_cancelled(scan_id):
                scan.status = "cancelled"
                scan.completed_at = utc_now()
                await record_scan_event(
                    db, scan.id, "scan_cancelled", {"message": "Scan cancelled by user"}
                )
                await db.commit()
                return

            if crawled_page.error:
                # Failed crawl page
                await persist_page_audit_results(
                    db,
                    scan_id=scan.id,
                    url=crawled_page.url,
                    normalized_url=crawled_page.url,
                    audit_result=execute_axe_audit(browser_page),  # type: ignore[arg-type]
                    audit_status="failed",
                    error_code="PAGE_CRAWL_FAILED",
                    error_summary=crawled_page.error,
                )
                await record_scan_event(
                    db,
                    scan.id,
                    "page_audited",
                    {
                        "url": crawled_page.url,
                        "audit_status": "failed",
                        "error": crawled_page.error,
                        "violations": 0,
                    },
                )
                await db.commit()
                continue

            # Navigate and audit
            try:
                await browser_page.goto(crawled_page.url, wait_until="domcontentloaded")
                audit_result = await execute_axe_audit(browser_page)

                await persist_page_audit_results(
                    db,
                    scan_id=scan.id,
                    url=crawled_page.url,
                    normalized_url=crawled_page.url,
                    audit_result=audit_result,
                    page_title=crawled_page.title,
                    http_status=crawled_page.status_code,
                    load_duration_ms=int(crawled_page.load_duration_ms),
                    audit_status="completed",
                )
                await record_scan_event(
                    db,
                    scan.id,
                    "page_audited",
                    {
                        "url": crawled_page.url,
                        "audit_status": "completed",
                        "violations": len(audit_result.violations),
                        "incomplete": len(audit_result.incomplete),
                    },
                )
                await db.commit()
            except Exception as e:
                logger.warning("Failed to audit page with axe", url=crawled_page.url, error=str(e))

    # --- Stage 4: Completed ---
    await db.refresh(scan)
    final_status = "completed_with_errors" if scan.pages_failed > 0 else "completed"
    scan.status = final_status
    scan.completed_at = utc_now()
    await db.commit()

    await record_scan_event(
        db,
        scan.id,
        "scan_completed",
        {
            "status": final_status,
            "total_pages": scan.total_pages,
            "pages_succeeded": scan.pages_succeeded,
            "pages_failed": scan.pages_failed,
            "total_violations": scan.total_violations,
        },
    )
    await db.commit()
    logger.info(
        "Scan completed successfully",
        scan_id=str(scan.id),
        status=final_status,
        pages=scan.total_pages,
        violations=scan.total_violations,
    )


@celery_app.task(bind=True, max_retries=3, default_retry_delay=5)
def run_scan_task(self: Any, scan_id_str: str) -> None:
    """Celery background scan orchestration task."""
    try:
        scan_uuid = uuid.UUID(scan_id_str)
        asyncio.run(execute_scan_pipeline(scan_uuid))
    except Exception as exc:
        logger.exception(
            "Scan background task failed with unexpected exception", scan_id=scan_id_str
        )
        raise self.retry(exc=exc) from exc
