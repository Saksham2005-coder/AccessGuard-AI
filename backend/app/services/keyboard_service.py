"""Keyboard Navigation Service.

Phase 19 Feature 5: Orchestrates deterministic keyboard navigation testing,
caching, and tenant authorization.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.core.logging import get_logger
from app.db.models.finding import Finding
from app.db.models.scan_page import ScanPage
from app.scanner.keyboard_extractor import run_keyboard_navigation_test
from app.schemas.keyboard_test import KeyboardNavigationReport
from app.services.scan_persistence_service import get_scan
from app.services.storage_service import (
    load_keyboard_test,
    resolve_artifact_path,
    save_keyboard_test,
)

logger = get_logger("keyboard_service")


async def get_or_run_keyboard_test(
    db: AsyncSession,
    *,
    scan_id: uuid.UUID,
    page_id: uuid.UUID,
    user_id: uuid.UUID,
    force_refresh: bool = False,
) -> KeyboardNavigationReport:
    """Retrieve or compute keyboard navigation test results with tenant authorization."""
    # 1. Authorize tenant via scan ownership
    scan = await get_scan(db, scan_id, user_id)

    # 2. Verify page exists and belongs to scan
    page_result = await db.execute(
        select(ScanPage).where(ScanPage.id == page_id, ScanPage.scan_id == scan.id)
    )
    page = page_result.scalar_one_or_none()
    if page is None:
        raise NotFoundError("Audited page record not found.")

    # 3. Check cached report if rerun not requested
    if not force_refresh:
        cached_json = load_keyboard_test(scan.id, page.id)
        if cached_json:
            try:
                return KeyboardNavigationReport.model_validate_json(cached_json)
            except Exception as e:
                logger.warning("Failed to deserialize cached keyboard report", error=str(e))

    # 4. Load page HTML snapshot from storage
    html_content: str | None = None
    if page.dom_snapshot_storage_key:
        artifact_path = resolve_artifact_path(page.dom_snapshot_storage_key)
        if artifact_path and artifact_path.is_file():
            html_content = artifact_path.read_text(encoding="utf-8", errors="replace")

    if not html_content:
        # Load findings to enrich fallback DOM
        findings_result = await db.execute(
            select(Finding).where(Finding.scan_page_id == page.id).order_by(Finding.created_at.asc())
        )
        findings = list(findings_result.scalars().all())

        elements_html: list[str] = [
            f"<header><h1>{page.page_title or 'Audited Web Page'}</h1></header>",
            "<main>",
            f"<p>Source URL: <a href='{page.url}'>{page.url}</a></p>",
        ]
        for f in findings:
            if f.html_snippet:
                elements_html.append(f"<div class='finding-node'>{f.html_snippet}</div>")
        elements_html.append("</main>")

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="utf-8"><title>{page.page_title or 'Audited Web Page'}</title></head>
<body>
{"".join(elements_html)}
</body>
</html>"""

    # 5. Execute keyboard navigation testing harness
    viewport_width = getattr(page, "viewport_width", 1280) or 1280
    viewport_height = getattr(page, "viewport_height", 800) or 800

    report = await run_keyboard_navigation_test(
        html_content=html_content,
        page_url=page.url,
        scan_id=scan.id,
        page_id=page.id,
        viewport_width=viewport_width,
        viewport_height=viewport_height,
    )

    # 6. Save report in storage for future instant retrieval
    try:
        save_keyboard_test(scan.id, page.id, report.model_dump_json())
    except Exception as e:
        logger.warning("Failed to persist keyboard test report", error=str(e))

    return report
