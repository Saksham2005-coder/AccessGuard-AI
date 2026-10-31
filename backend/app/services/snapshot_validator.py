"""Isolated DOM snapshot validation service running local axe-core audits on patched HTML."""

import time
from typing import Any

from app.core.logging import get_logger
from app.scanner.axe_runner import execute_axe_audit, get_axe_version
from app.scanner.browser import BrowserManager
from app.services.snapshot_service import (
    apply_dom_patch,
    compute_patch_hash,
    compute_snapshot_hash,
    sanitize_dom_snapshot,
)

logger = get_logger("snapshot_validator")

# Global singleton browser manager for isolated snapshot validation runs
_snapshot_browser_manager: BrowserManager | None = None


def get_snapshot_browser_manager() -> BrowserManager:
    """Return shared BrowserManager for headless snapshot validations."""
    global _snapshot_browser_manager
    if _snapshot_browser_manager is None:
        _snapshot_browser_manager = BrowserManager()
    return _snapshot_browser_manager


class SnapshotValidator:
    """Orchestrates isolated DOM snapshot reconstruction, patch application, and axe-core validation."""

    def __init__(self, browser_manager: BrowserManager | None = None) -> None:
        self.browser_manager = browser_manager or get_snapshot_browser_manager()

    async def validate_snapshot(
        self,
        snapshot_html: str,
        original_rule_id: str,
        patch_operations: list[dict[str, Any]],
        finding_id: str | None = None,
    ) -> dict[str, Any]:
        """Validate an accessibility patch against a sanitized, isolated DOM snapshot.

        Guarantees:
        - Network routes are strictly aborted; remote scripts, images, and fonts are NEVER loaded.
        - Only allowlisted DOM patch operations are applied.
        - Original rule resolution and regression of new violations are strictly evaluated.
        - Labeled accurately as snapshot validation; never claims live website is fixed.
        """
        start_time = time.monotonic()
        snapshot_hash = compute_snapshot_hash(snapshot_html)
        patch_hash = compute_patch_hash(patch_operations)
        axe_ver = get_axe_version()

        # Wrap component snippet in valid document structure if needed for clean axe auditing
        effective_html = snapshot_html.strip()
        if "<html" not in effective_html.lower():
            effective_html = (
                '<!DOCTYPE html>\n<html lang="en">\n<head>\n'
                '  <meta charset="utf-8">\n'
                "  <title>Isolated Accessibility Snapshot</title>\n"
                "</head>\n<body>\n"
                "  <main>\n"
                "    <h1>Isolated Accessibility Snapshot</h1>\n"
                f"    {effective_html}\n"
                "  </main>\n"
                "</body>\n</html>"
            )

        # 1. Sanitize DOM snapshot to purge remote scripts and trackers
        sanitized_html = sanitize_dom_snapshot(effective_html)

        # 2. Apply allowlisted DOM operations
        try:
            patched_html, applied_logs = apply_dom_patch(sanitized_html, patch_operations)
        except Exception as patch_err:
            logger.warning(
                "DOM patch application failed safety policy",
                error=str(patch_err),
                finding_id=finding_id,
            )
            return {
                "validation_mode": "dom_snapshot",
                "passed": False,
                "original_rule_resolved": False,
                "new_violations": [],
                "details": {
                    "error": str(patch_err),
                    "policy_violation": True,
                    "snapshot_hash": snapshot_hash,
                    "patch_hash": patch_hash,
                    "axe_version": axe_ver,
                    "label": "Snapshot validation failed: Patch operations violated safety policy.",
                },
            }

        # 3. Launch isolated Playwright page with network loading disabled
        browser = await self.browser_manager.get_browser()
        context = await browser.new_context(
            bypass_csp=False,
            java_script_enabled=True,
        )
        page = await context.new_page()

        try:
            # Strictly abort all external network requests
            await page.route("**/*", lambda route: route.abort())

            # Set sanitized, patched HTML content into isolated document
            await page.set_content(patched_html, wait_until="domcontentloaded")

            # 4. Execute pinned local axe-core audit
            audit_result = await execute_axe_audit(page)

            # 5. Evaluate original rule resolution and new violations
            violations = audit_result.violations

            # Check if original violation still reproduces
            original_rule_still_failing = any(v.rule_id == original_rule_id for v in violations)
            original_rule_resolved = not original_rule_still_failing

            # Collect any other violations introduced (regressions)
            new_violations: list[dict[str, Any]] = [
                {
                    "rule_id": v.rule_id,
                    "impact": v.impact,
                    "description": v.description,
                    "primary_selector": v.primary_selector,
                }
                for v in violations
                if v.rule_id != original_rule_id
            ]

            passed = original_rule_resolved and len(new_violations) == 0
            duration_ms = int((time.monotonic() - start_time) * 1000)

            label = (
                "Snapshot validation passed: Applicable automated rule resolved in isolated snapshot without introducing new violations."
                if passed
                else "Snapshot validation failed: Rule not resolved or new accessibility violations introduced."
            )

            logger.info(
                "Completed snapshot validation",
                passed=passed,
                original_rule_resolved=original_rule_resolved,
                new_violations_count=len(new_violations),
                duration_ms=duration_ms,
            )

            return {
                "validation_mode": "dom_snapshot",
                "passed": passed,
                "original_rule_resolved": original_rule_resolved,
                "new_violations": new_violations,
                "details": {
                    "label": label,
                    "axe_version": axe_ver,
                    "snapshot_hash": snapshot_hash,
                    "patch_hash": patch_hash,
                    "duration_ms": duration_ms,
                    "applied_operations_count": len(applied_logs),
                    "applied_operations": applied_logs,
                    "passes_count": audit_result.passes_count,
                    "incomplete_count": len(audit_result.incomplete),
                },
            }
        finally:
            await page.close()
            await context.close()
