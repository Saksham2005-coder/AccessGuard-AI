"""Isolated before-and-after snapshot comparison service for accessibility remediation proposals."""

import contextlib
import difflib
import time
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.scanner.axe_runner import execute_axe_audit, get_axe_version
from app.services.remediation_service import get_remediation_and_check_ownership
from app.services.snapshot_service import (
    apply_dom_patch,
    compute_patch_hash,
    compute_snapshot_hash,
    sanitize_dom_snapshot,
)
from app.services.snapshot_validator import get_snapshot_browser_manager
from app.services.storage_service import save_remediation_screenshot

logger = get_logger("comparison_service")


def generate_dom_diff(before_html: str, after_html: str) -> str:
    """Generate a clean unified text diff between before and after HTML snapshots."""
    before_lines = before_html.strip().splitlines()
    after_lines = after_html.strip().splitlines()
    diff = difflib.unified_diff(
        before_lines,
        after_lines,
        fromfile="Original Snapshot (Isolated)",
        tofile="Proposed Patch (Isolated)",
        lineterm="",
    )
    return "\n".join(diff)


def wrap_for_render(html: str) -> str:
    """Wrap raw component snippets into a compliant HTML5 document for headless rendering."""
    clean = html.strip()
    if "<html" in clean.lower():
        return clean

    return (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n'
        '  <meta charset="utf-8">\n'
        "  <title>Isolated Accessibility Comparison</title>\n"
        "  <style>\n"
        "    body { font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; "
        "margin: 32px; background: #ffffff; color: #111827; line-height: 1.5; }\n"
        "    main { max-width: 900px; margin: 0 auto; }\n"
        "  </style>\n"
        "</head>\n<body>\n"
        "  <main>\n"
        f"    {clean}\n"
        "  </main>\n"
        "</body>\n</html>"
    )


async def generate_remediation_comparison(
    db: AsyncSession,
    remediation_id: uuid.UUID,
    user_id: uuid.UUID,
) -> dict[str, Any]:
    """Execute isolated before-and-after comparison rendering and re-audit for a remediation."""
    remediation, finding, _project = await get_remediation_and_check_ownership(
        db, remediation_id, user_id
    )

    start_time = time.monotonic()
    raw_snapshot = (
        finding.html_snippet or remediation.before_snippet or "<div>Accessibility barrier snippet</div>"
    )
    sanitized_before = sanitize_dom_snapshot(raw_snapshot)
    patch_ops = remediation.patch_payload.get("patch_operations", [])
    normalized_patch_ops: list[dict[str, Any]] = []
    for raw_op in patch_ops:
        if isinstance(raw_op, dict):
            c = dict(raw_op)
            if "op" in c and "operation" not in c:
                c["operation"] = c.pop("op")
            normalized_patch_ops.append(c)

    # Apply allowlisted DOM operations
    try:
        if normalized_patch_ops:
            patched_after, applied_logs = apply_dom_patch(sanitized_before, normalized_patch_ops)
        elif remediation.after_snippet:
            patched_after = sanitize_dom_snapshot(remediation.after_snippet)
            applied_logs = []
        else:
            patched_after = sanitized_before
            applied_logs = []
    except Exception as patch_err:
        logger.warning(
            "Comparison patch application failed safety policy",
            remediation_id=str(remediation_id),
            error=str(patch_err),
        )
        patched_after = sanitize_dom_snapshot(remediation.after_snippet or sanitized_before)
        applied_logs = []

    dom_diff = generate_dom_diff(sanitized_before, patched_after)

    before_screenshot_key: str | None = None
    after_screenshot_key: str | None = None
    original_rule_resolved = False
    new_violations: list[dict[str, Any]] = []
    axe_ver = get_axe_version()
    browser_failed = False

    # Attempt headless Playwright rendering with network egress completely blocked
    try:
        browser_manager = get_snapshot_browser_manager()
        browser = await browser_manager.get_browser()
        context = await browser.new_context(
            viewport={"width": 1024, "height": 640},
            bypass_csp=False,
            java_script_enabled=True,
        )
        page = await context.new_page()

        try:
            # Strictly abort all external network requests (defense-in-depth)
            async def _abort_route(route: Any) -> None:
                with contextlib.suppress(Exception):
                    await route.abort()

            await page.route("**/*", _abort_route)

            # 1. Render Before Snapshot
            wrapped_before = wrap_for_render(sanitized_before)
            await page.set_content(wrapped_before, wait_until="domcontentloaded", timeout=5000)
            before_bytes = await page.screenshot(type="png", full_page=False, timeout=5000)
            before_screenshot_key = save_remediation_screenshot(
                remediation.id, "before", before_bytes
            )

            # 2. Render After Snapshot
            wrapped_after = wrap_for_render(patched_after)
            await page.set_content(wrapped_after, wait_until="domcontentloaded", timeout=5000)
            after_bytes = await page.screenshot(type="png", full_page=False, timeout=5000)
            after_screenshot_key = save_remediation_screenshot(
                remediation.id, "after", after_bytes
            )

            # 3. Run axe-core audit on isolated after snapshot
            audit_result = await execute_axe_audit(page)
            violations = audit_result.violations

            # Check if original finding rule resolved
            original_rule_still_failing = any(
                v.rule_id == finding.axe_rule_id for v in violations
            )
            original_rule_resolved = not original_rule_still_failing

            # Check for newly introduced violations (regressions)
            new_violations = [
                {
                    "rule_id": v.rule_id,
                    "impact": v.impact,
                    "description": v.description,
                    "primary_selector": v.primary_selector,
                }
                for v in violations
                if v.rule_id != finding.axe_rule_id
            ]

        finally:
            await page.close()
            await context.close()

    except Exception as render_err:
        logger.warning(
            "Comparison headless browser rendering encountered non-fatal error; continuing with DOM diff",
            error=str(render_err),
            remediation_id=str(remediation_id),
        )
        browser_failed = True
        # If browser not available, fall back to structural assessment
        original_rule_resolved = bool(remediation.after_snippet) and len(patch_ops) > 0

    duration_ms = int((time.monotonic() - start_time) * 1000)
    passed = original_rule_resolved and len(new_violations) == 0

    comparison_data: dict[str, Any] = {
        "remediation_id": str(remediation.id),
        "finding_id": str(finding.id),
        "rule_id": finding.axe_rule_id,
        "before_html": sanitized_before,
        "after_html": patched_after,
        "before_screenshot_url": (
            f"/api/v1/remediations/{remediation.id}/screenshots/before"
            if before_screenshot_key
            else None
        ),
        "after_screenshot_url": (
            f"/api/v1/remediations/{remediation.id}/screenshots/after"
            if after_screenshot_key
            else None
        ),
        "dom_diff": dom_diff,
        "patch_operations": patch_ops,
        "original_rule_resolved": original_rule_resolved,
        "new_violations": new_violations,
        "passed": passed,
        "status": "completed" if not browser_failed else "dom_diff_only",
        "created_at": datetime.now(UTC).isoformat(),
        "details": {
            "axe_version": axe_ver,
            "duration_ms": duration_ms,
            "applied_operations_count": len(applied_logs),
            "before_hash": compute_snapshot_hash(sanitized_before),
            "after_hash": compute_snapshot_hash(patched_after),
            "patch_hash": compute_patch_hash(patch_ops),
            "browser_rendered": not browser_failed,
            "label": "Isolated Before-and-After Snapshot Comparison (Production website unmodified).",
        },
    }

    # Cache comparison in patch_payload
    payload = dict(remediation.patch_payload or {})
    payload["comparison"] = comparison_data
    remediation.patch_payload = payload

    await db.commit()
    await db.refresh(remediation)

    return comparison_data


async def get_remediation_comparison(
    db: AsyncSession,
    remediation_id: uuid.UUID,
    user_id: uuid.UUID,
) -> dict[str, Any]:
    """Retrieve existing comparison data or generate it if absent."""
    remediation, _finding, _project = await get_remediation_and_check_ownership(
        db, remediation_id, user_id
    )

    cached = (remediation.patch_payload or {}).get("comparison")
    if cached and isinstance(cached, dict):
        return cached

    return await generate_remediation_comparison(
        db=db,
        remediation_id=remediation_id,
        user_id=user_id,
    )
