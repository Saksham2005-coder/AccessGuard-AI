"""Unit tests for Accessibility Regression Monitoring.

Phase 19 Feature 6: Stable versioned finding fingerprints, coverage-aware comparison,
pinned baselines, scheduled audits, and notifications.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.errors import PolicyViolationError
from app.db.models.finding import Finding
from app.db.models.scan import Scan
from app.db.models.scan_page import ScanPage
from app.schemas.regression import ScanScheduleCreate
from app.services import regression_service
from app.services.regression_service import (
    compute_finding_fingerprint,
    normalize_url,
)


def test_normalize_url_strips_tracking_and_canonicalizes() -> None:
    """Verify URL canonicalization cleans query tracking parameters and normalizes paths."""
    url1 = "https://Example.COM:443/products/item/?utm_source=twitter&utm_medium=cpc&id=123#reviews"
    url2 = "https://example.com/products/item?id=123"

    assert normalize_url(url1) == "https://example.com/products/item?id=123"
    assert normalize_url(url1) == normalize_url(url2)


def test_compute_finding_fingerprint_versioned_and_stable() -> None:
    """Verify deterministic versioned fingerprint generation across normalized variations."""
    fp1 = compute_finding_fingerprint(
        canonical_url="https://example.com/about",
        axe_rule_id="color-contrast",
        selector="div > p.description",
        html_snippet="<p class='description'>Text</p>",
        impact="serious",
    )
    fp2 = compute_finding_fingerprint(
        canonical_url="https://example.com/about",
        axe_rule_id="color-contrast",
        selector="  div  >   p.description  ",
        html_snippet="<P class='description'>Text</P>",
        impact="serious",
    )

    assert fp1.startswith("v1:")
    assert fp1 == fp2


@pytest.mark.asyncio
async def test_regression_comparison_classifications() -> None:
    """Verify new, resolved, persistent, changed, and inconclusive findings are classified properly."""
    project_id = uuid.uuid4()
    user_id = uuid.uuid4()
    curr_scan_id = uuid.uuid4()
    base_scan_id = uuid.uuid4()

    curr_page_id = uuid.uuid4()
    base_page1_id = uuid.uuid4()
    base_page2_id = uuid.uuid4()  # Page missing in current scan!

    curr_scan = Scan(
        id=curr_scan_id,
        project_id=project_id,
        requested_by=user_id,
        target_url="https://example.com",
        status="completed",
    )
    base_scan = Scan(
        id=base_scan_id,
        project_id=project_id,
        requested_by=user_id,
        target_url="https://example.com",
        status="completed",
    )

    page_url_shared = "https://example.com/home"
    page_url_missing = "https://example.com/unscanned-page"

    # Persistent finding (shared between both)
    f_persistent_curr = Finding(
        id=uuid.uuid4(),
        scan_page_id=curr_page_id,
        axe_rule_id="image-alt",
        impact="critical",
        description="Missing alt",
        selector="img#logo",
        html_snippet="<img id='logo'>",
        wcag_tags=["wcag111"],
    )
    f_persistent_base = Finding(
        id=uuid.uuid4(),
        scan_page_id=base_page1_id,
        axe_rule_id="image-alt",
        impact="critical",
        description="Missing alt",
        selector="img#logo",
        html_snippet="<img id='logo'>",
        wcag_tags=["wcag111"],
    )

    # Changed finding (same rule and selector, changed impact)
    f_changed_curr = Finding(
        id=uuid.uuid4(),
        scan_page_id=curr_page_id,
        axe_rule_id="color-contrast",
        impact="critical",
        description="Low contrast",
        selector="button.cta",
        html_snippet="<button class='cta'>Click</button>",
        wcag_tags=["wcag143"],
    )
    f_changed_base = Finding(
        id=uuid.uuid4(),
        scan_page_id=base_page1_id,
        axe_rule_id="color-contrast",
        impact="minor",
        description="Low contrast",
        selector="button.cta",
        html_snippet="<button class='cta'>Click</button>",
        wcag_tags=["wcag143"],
    )

    # New finding (only in current scan)
    f_new_curr = Finding(
        id=uuid.uuid4(),
        scan_page_id=curr_page_id,
        axe_rule_id="aria-label",
        impact="moderate",
        description="Missing label",
        selector="nav > a",
        html_snippet="<a>Link</a>",
        wcag_tags=["wcag412"],
    )

    # Resolved finding (in baseline on shared page, absent in current)
    f_resolved_base = Finding(
        id=uuid.uuid4(),
        scan_page_id=base_page1_id,
        axe_rule_id="document-title",
        impact="serious",
        description="Document title missing",
        selector="html",
        html_snippet="<html>",
        wcag_tags=["wcag242"],
    )

    # Inconclusive finding (on missing page)
    f_inconclusive_base = Finding(
        id=uuid.uuid4(),
        scan_page_id=base_page2_id,
        axe_rule_id="link-name",
        impact="serious",
        description="Empty link",
        selector="footer a",
        html_snippet="<a></a>",
        wcag_tags=["wcag412"],
    )

    db_mock = AsyncMock()

    pages_call_count = 0
    findings_call_count = 0

    async def mock_execute(stmt):
        nonlocal pages_call_count, findings_call_count
        stmt_str = str(stmt)
        res = MagicMock()
        if "FROM scan_pages" in stmt_str:
            pages_call_count += 1
            if pages_call_count == 1:
                res.scalars.return_value.all.return_value = [
                    ScanPage(id=curr_page_id, scan_id=curr_scan_id, url=page_url_shared)
                ]
            else:
                res.scalars.return_value.all.return_value = [
                    ScanPage(id=base_page1_id, scan_id=base_scan_id, url=page_url_shared),
                    ScanPage(id=base_page2_id, scan_id=base_scan_id, url=page_url_missing),
                ]
            return res
        elif "FROM findings" in stmt_str:
            findings_call_count += 1
            if findings_call_count == 1:
                res.all.return_value = [
                    (f_persistent_curr, page_url_shared),
                    (f_changed_curr, page_url_shared),
                    (f_new_curr, page_url_shared),
                ]
            else:
                res.all.return_value = [
                    (f_persistent_base, page_url_shared),
                    (f_changed_base, page_url_shared),
                    (f_resolved_base, page_url_shared),
                    (f_inconclusive_base, page_url_missing),
                ]
            return res
        return res

    db_mock.execute.side_effect = mock_execute

    with patch("app.services.regression_service.get_scan", side_effect=[curr_scan, base_scan]):
        report = await regression_service.compare_scans(
            db=db_mock,
            project_id=project_id,
            current_scan_id=curr_scan_id,
            baseline_scan_id=base_scan_id,
            user_id=user_id,
        )

    assert report.coverage.coverage_status == "partial"
    assert report.coverage.missing_pages_count == 1
    assert report.summary.new_count == 1
    assert report.summary.resolved_count == 1
    assert report.summary.persistent_count == 1
    assert report.summary.changed_count == 1
    assert report.summary.inconclusive_count == 1
    assert report.summary.net_change == 0  # 1 new - 1 resolved


@pytest.mark.asyncio
async def test_schedule_creation_requires_domain_verification() -> None:
    """Verify recurring scan creation is denied if domain is unverified."""
    db_mock = AsyncMock()
    project_id = uuid.uuid4()
    user_id = uuid.uuid4()
    payload = ScanScheduleCreate(cadence="weekly", target_url="https://example.com")

    with (
        patch("app.services.regression_service.get_project_verification_status", return_value=False),
        pytest.raises(PolicyViolationError, match="Domain verification is mandatory"),
    ):
        await regression_service.create_scan_schedule(
            db=db_mock,
            project_id=project_id,
            user_id=user_id,
            data=payload,
        )
