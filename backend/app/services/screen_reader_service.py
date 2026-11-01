"""Service layer managing screen-reader-oriented page reading simulation with tenant authorization."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundError
from app.core.logging import get_logger
from app.db.models.finding import Finding
from app.db.models.scan_page import ScanPage
from app.scanner.screen_reader_extractor import extract_semantic_tree_from_html
from app.schemas.screen_reader import ScreenReaderSimulationResponse
from app.services.scan_persistence_service import get_scan
from app.services.storage_service import (
    load_screen_reader_simulation,
    resolve_artifact_path,
    save_screen_reader_simulation,
)

logger = get_logger("screen_reader_service")


async def get_or_create_page_simulation(
    db: AsyncSession,
    *,
    scan_id: uuid.UUID,
    page_id: uuid.UUID,
    user_id: uuid.UUID,
    force_refresh: bool = False,
) -> ScreenReaderSimulationResponse:
    """Retrieve or evaluate screen-reader-oriented semantic reading preview for an audited page."""
    # Enforce tenant isolation via scan
    scan = await get_scan(db, scan_id, user_id)

    # Load page record
    page_result = await db.execute(
        select(ScanPage).where(ScanPage.id == page_id, ScanPage.scan_id == scan.id)
    )
    page = page_result.scalar_one_or_none()
    if page is None:
        raise NotFoundError("Audited page record not found.")

    # Check cache if not forcing refresh
    if not force_refresh:
        cached_json = load_screen_reader_simulation(scan.id, page.id)
        if cached_json:
            try:
                return ScreenReaderSimulationResponse.model_validate_json(cached_json)
            except Exception as e:
                logger.warning("Failed to deserialize cached screen reader simulation", error=str(e))

    # Load findings for this page to correlate selectors and accessible name violations
    findings_result = await db.execute(
        select(Finding).where(Finding.scan_page_id == page.id).order_by(Finding.created_at.asc())
    )
    findings = list(findings_result.scalars().all())

    # Obtain HTML content from DOM snapshot or generate synthetic preview from findings
    html_content: str | None = None
    if page.dom_snapshot_storage_key:
        artifact_path = resolve_artifact_path(page.dom_snapshot_storage_key)
        if artifact_path and artifact_path.is_file():
            html_content = artifact_path.read_text(encoding="utf-8", errors="replace")

    if not html_content:
        # Build clean semantic representation from page metadata and finding snippets
        elements_html: list[str] = []
        elements_html.append(f"<header role='banner'><h1>{page.page_title or 'Audited Web Page'}</h1></header>")
        elements_html.append("<main role='main'>")

        for f in findings:
            if f.html_snippet and len(f.html_snippet.strip()) > 3:
                elements_html.append(f.html_snippet)
            elif f.axe_rule_id == "image-alt":
                elements_html.append('<img src="/placeholder.png" alt="" />')
            elif f.axe_rule_id == "button-name":
                elements_html.append('<button type="button"></button>')
            elif f.axe_rule_id == "heading-order":
                elements_html.append("<h3>Skipped Section Heading</h3>")
            elif f.axe_rule_id == "label":
                elements_html.append('<input type="text" id="unlabeled-field" />')

        elements_html.append("</main>")
        html_content = "\n".join(elements_html)

    simulation = await extract_semantic_tree_from_html(
        html_content=html_content,
        findings=findings,
        page_url=page.url,
        scan_id=str(scan.id),
        page_id=str(page.id),
    )

    # Cache simulation artifact
    save_screen_reader_simulation(scan.id, page.id, simulation.model_dump_json())

    logger.info(
        "Generated screen reader simulation preview",
        scan_id=str(scan.id),
        page_id=str(page.id),
        nodes_count=simulation.nodes_count,
        hints_count=len(simulation.review_hints),
    )

    return simulation
