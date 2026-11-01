"""Unit tests for Keyboard Navigation Simulator.

Phase 19 Feature 5: Deterministic keyboard-only navigation testing,
activeElement tracking, focus indicator evidence, and trap detection.
"""

import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.core.errors import NotFoundError
from app.scanner.keyboard_extractor import run_keyboard_navigation_test
from app.services import keyboard_service


@pytest.mark.asyncio
async def test_keyboard_extractor_traversal_and_issues() -> None:
    """Verify deterministic Tab traversal, focus indicator detection, and issue tagging."""
    html_fixture = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Keyboard Test Page</title>
    <style>
        .styled-btn {
            outline: 2px solid #2563eb;
            outline-offset: 2px;
        }
        .bad-btn {
            outline: none;
            box-shadow: none;
            border: none;
        }
    </style>
</head>
<body>
    <header>
        <a id="nav-link" href="#main" aria-label="Skip to content" class="styled-btn">Skip</a>
    </header>
    <main id="main">
        <button id="btn-valid" class="styled-btn">Submit Order</button>
        <button id="btn-no-name" class="bad-btn"></button>
        <input id="tabindex-input" type="text" placeholder="Your name" tabindex="5" />
    </main>
</body>
</html>"""

    report = await run_keyboard_navigation_test(
        html_content=html_fixture,
        page_url="https://example.com/keyboard",
        max_forward_steps=10,
        max_reverse_steps=5,
    )

    assert report.page_url == "https://example.com/keyboard"
    assert report.summary.forward_steps >= 3
    assert len(report.steps) >= 3

    # Check forward steps
    step_tags = [s.tag_name for s in report.steps]
    assert "a" in step_tags
    assert "button" in step_tags

    # Check issues detected
    issue_types = {i.issue_type for i in report.issues}
    assert "missing_accessible_name" in issue_types
    assert "missing_focus_indicator" in issue_types
    assert "positive_tabindex" in issue_types

    # Find the bad button issues
    bad_btn_issues = [i for i in report.issues if "btn-no-name" in i.selector]
    assert len(bad_btn_issues) >= 1
    assert any(i.issue_type == "missing_accessible_name" for i in bad_btn_issues)
    assert any(i.issue_type == "missing_focus_indicator" for i in bad_btn_issues)

    # Positive tabindex issue
    pos_issues = [i for i in report.issues if i.issue_type == "positive_tabindex"]
    assert len(pos_issues) == 1
    assert "5" in pos_issues[0].message


@pytest.mark.asyncio
async def test_keyboard_extractor_privacy_redaction() -> None:
    """Verify password inputs are never leaked in accessible names or reports."""
    html_fixture = """<!DOCTYPE html>
<html lang="en">
<body>
    <form>
        <input type="password" id="pwd" value="SecretPasswordP@ssword123" />
        <button id="submit">Login</button>
    </form>
</body>
</html>"""

    report = await run_keyboard_navigation_test(
        html_content=html_fixture,
        page_url="https://example.com/login",
        max_forward_steps=5,
    )

    pwd_steps = [s for s in report.steps if "pwd" in s.selector]
    assert len(pwd_steps) == 1
    assert pwd_steps[0].accessible_name == "[REDACTED_SECURE_FIELD]"
    assert "SecretPassword" not in report.model_dump_json()


@pytest.mark.asyncio
async def test_keyboard_tenant_isolation() -> None:
    """Verify cross-tenant requests are strictly blocked with NotFoundError."""
    db_mock = AsyncMock()
    scan_id = uuid.uuid4()
    page_id = uuid.uuid4()
    user_id = uuid.uuid4()

    with (
        patch("app.services.keyboard_service.get_scan", side_effect=NotFoundError("Scan record not found or inaccessible.")),
        pytest.raises(NotFoundError, match="Scan record not found"),
    ):
        await keyboard_service.get_or_run_keyboard_test(
            db=db_mock,
            scan_id=scan_id,
            page_id=page_id,
            user_id=user_id,
        )
