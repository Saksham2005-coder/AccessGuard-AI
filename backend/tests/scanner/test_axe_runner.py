"""Unit and integration tests for axe-core bundle resolution, injection, and rule evaluation."""

import pytest

from app.scanner.axe_runner import (
    compute_finding_fingerprint,
    execute_axe_audit,
    filter_wcag_tags,
    get_axe_bundle_path,
    get_axe_version,
)
from app.scanner.browser import create_isolated_browser_context


def test_axe_bundle_path_and_version() -> None:
    """Verify local axe-core bundle exists without needing public CDN."""
    bundle_path = get_axe_bundle_path()
    assert bundle_path.exists(), f"Bundle file missing at {bundle_path}"
    assert bundle_path.suffix == ".js"

    version = get_axe_version()
    assert version.startswith("4."), f"Unexpected axe-core version: {version}"


def test_filter_wcag_tags() -> None:
    """Verify separation of official WCAG criterion tags from best practices."""
    raw_tags = ["cat.text-alternatives", "wcag2a", "wcag111", "best-practice", "section508"]
    wcag_tags, is_best_practice = filter_wcag_tags(raw_tags)

    assert "wcag2a" in wcag_tags
    assert "wcag111" in wcag_tags
    assert "section508" in wcag_tags
    assert "best-practice" not in wcag_tags
    assert is_best_practice is True


def test_fingerprint_deterministic_and_unique() -> None:
    """Verify fingerprint is stable for identical elements and unique for different elements."""
    fp1 = compute_finding_fingerprint(
        "https://example.com/", "image-alt", "img#logo", '<img id="logo">'
    )
    fp2 = compute_finding_fingerprint(
        "https://example.com/", "image-alt", "img#logo", '<img id="logo">'
    )
    # Identical element yields identical fingerprint
    assert fp1 == fp2

    # Different selector or snippet yields different fingerprint
    fp3 = compute_finding_fingerprint(
        "https://example.com/", "image-alt", "img#banner", '<img id="banner">'
    )
    assert fp1 != fp3


@pytest.mark.asyncio
async def test_axe_detects_real_violations_on_inaccessible_fixture() -> None:
    """Verify axe-core detects real violations (missing alt, empty button) on local HTML."""
    inaccessible_html = """<!DOCTYPE html>
    <html lang="en">
    <head><title>Test Inaccessible Page</title></head>
    <body>
        <h1>Accessibility Test</h1>
        <!-- Violation 1: Image without alt text -->
        <img id="test-banner" src="banner.jpg" />
        <!-- Violation 2: Button without accessible name -->
        <button id="empty-action" type="button"></button>
    </body>
    </html>"""

    async with create_isolated_browser_context() as context:
        page = await context.new_page()
        await page.set_content(inaccessible_html)

        result = await execute_axe_audit(page)

        assert result.axe_version.startswith("4.")
        assert len(result.violations) >= 2

        rule_ids = [v.rule_id for v in result.violations]
        assert "image-alt" in rule_ids
        assert "button-name" in rule_ids

        # Check image-alt details
        img_violation = next(v for v in result.violations if v.rule_id == "image-alt")
        assert img_violation.impact in ("serious", "critical")
        assert "wcag111" in img_violation.wcag_tags or "wcag2a" in img_violation.wcag_tags
        assert len(img_violation.nodes) >= 1
        assert "img" in img_violation.nodes[0].html_snippet


@pytest.mark.asyncio
async def test_axe_clean_fixture_produces_no_violations() -> None:
    """Verify clean accessible page produces zero violations."""
    accessible_html = """<!DOCTYPE html>
    <html lang="en">
    <head><title>Accessible Demo</title></head>
    <body>
        <main>
            <h1>Accessible Title</h1>
            <p>This is a fully compliant accessible sample paragraph.</p>
            <img src="logo.png" alt="Company Logo" />
            <button type="button">Submit Feedback</button>
        </main>
    </body>
    </html>"""

    async with create_isolated_browser_context() as context:
        page = await context.new_page()
        await page.set_content(accessible_html)

        result = await execute_axe_audit(page)

        # Must not report fake violations
        assert len(result.violations) == 0
        assert result.passes_count > 0
