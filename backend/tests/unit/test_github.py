"""Unit tests for GitHub PR Integration.

Phase 19 Feature 7: Signature validation, delivery idempotency, PR review markdown generation,
and domain verification enforcement.
"""

import hashlib
import hmac
import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.errors import PolicyViolationError
from app.db.models.finding import Finding
from app.db.models.github import GitHubIntegration, GitHubReviewRecord
from app.db.models.project import Project
from app.db.models.scan import Scan
from app.schemas.github import TestReviewRequest
from app.services import github_service
from app.services.github_service import (
    format_pr_review_markdown,
    mask_secret,
    verify_webhook_signature,
)


def test_verify_webhook_signature_valid() -> None:
    """Verify that valid HMAC-SHA256 signatures are accepted."""
    secret = "test_webhook_secret_12345"
    payload = b'{"action":"opened","pull_request":{"number":42}}'
    digest = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    valid_header = f"sha256={digest}"

    assert verify_webhook_signature(payload, valid_header, secret) is True


def test_verify_webhook_signature_tampered_or_invalid() -> None:
    """Verify that tampered payloads or wrong secrets are rejected."""
    secret = "test_webhook_secret_12345"
    payload = b'{"action":"opened"}'
    valid_header = f"sha256={hmac.new(secret.encode('utf-8'), payload, hashlib.sha256).hexdigest()}"

    # Tampered payload
    assert verify_webhook_signature(b'{"action":"closed"}', valid_header, secret) is False

    # Wrong secret
    assert verify_webhook_signature(payload, valid_header, "wrong_secret") is False

    # Malformed header
    assert verify_webhook_signature(payload, "invalid_header", secret) is False
    assert verify_webhook_signature(payload, None, secret) is False


def test_mask_secret() -> None:
    """Verify secret masking only reveals short prefix/suffix."""
    secret = "whsec_0123456789abcdef0123"
    masked = mask_secret(secret)
    assert masked == "whsec_...0123"
    assert secret not in masked


def test_format_pr_review_markdown_includes_disclaimer_and_metrics() -> None:
    """Verify review comment includes breakdown, top violations, and legal disclaimer."""
    scan_page_id = uuid.uuid4()
    findings = [
        Finding(
            id=uuid.uuid4(),
            scan_page_id=scan_page_id,
            axe_rule_id="color-contrast",
            impact="critical",
            selector="button.cta-primary",
            description="Element has insufficient color contrast of 2.1:1",
        ),
        Finding(
            id=uuid.uuid4(),
            scan_page_id=scan_page_id,
            axe_rule_id="image-alt",
            impact="serious",
            selector="img.logo",
            description="Image element has no alt attribute",
        ),
    ]

    scan = Scan(
        id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        target_url="https://example.com/app",
        status="completed",
    )

    md = format_pr_review_markdown(
        project_name="Example App",
        target_url="https://example.com/app",
        scan=scan,
        findings=findings,
        pr_number=17,
        head_sha="9f8e7d6c5b4a",
    )

    assert "## 🛡️ AccessGuard AI — Accessibility Review" in md
    assert "**Project:** Example App" in md
    assert "**PR:** #17" in md
    assert "`9f8e7d6c`" in md
    assert "🔴 **Critical**" in md
    assert "color-contrast" in md
    assert "image-alt" in md
    assert "button.cta-primary" in md
    assert "Disclaimer:" in md
    assert "does not constitute a legal WCAG compliance certification" in md


@pytest.mark.asyncio
async def test_webhook_idempotency_prevents_duplicate_processing() -> None:
    """Verify that replaying a delivery ID returns duplicate status without reprocessing."""
    db = AsyncMock()
    existing_rec = GitHubReviewRecord(
        id=uuid.uuid4(),
        integration_id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        delivery_id="delivery-already-processed-123",
        pr_number=1,
        pr_title="PR 1",
        head_sha="sha1",
        base_sha="sha0",
        status="reviewed",
    )

    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = existing_rec
    db.execute.return_value = mock_res

    status_code, resp = await github_service.process_webhook_payload(
        db=db,
        delivery_id="delivery-already-processed-123",
        event_type="pull_request",
        signature_header="sha256=abcdef",
        raw_body=b'{"action":"opened"}',
    )

    assert status_code == 200
    assert resp.status == "duplicate"
    assert "already processed" in resp.message


@pytest.mark.asyncio
async def test_webhook_unverified_domain_skips_audit() -> None:
    """Verify that unverified target domain records review as skipped."""
    db = AsyncMock()
    project_id = uuid.uuid4()
    secret = "whsec_secret_123"

    payload_dict = {
        "action": "opened",
        "repository": {"owner": {"login": "acme-corp"}, "name": "portal"},
        "pull_request": {
            "number": 88,
            "title": "Add new dashboard",
            "user": {"login": "developer"},
            "head": {"sha": "sha_head_123"},
            "base": {"sha": "sha_base_123"},
        },
    }
    raw_body = json.dumps(payload_dict).encode("utf-8")
    sig = f"sha256={hmac.new(secret.encode('utf-8'), raw_body, hashlib.sha256).hexdigest()}"

    # 1st execute: delivery check (None)
    # 2nd execute: integration lookup (integration)
    integration = GitHubIntegration(
        id=uuid.uuid4(),
        project_id=project_id,
        repo_owner="acme-corp",
        repo_name="portal",
        webhook_secret=secret,
        enabled=True,
        auto_review_prs=True,
        created_by=uuid.uuid4(),
    )

    mock_delivery_res = MagicMock()
    mock_delivery_res.scalar_one_or_none.return_value = None

    mock_integ_res = MagicMock()
    mock_integ_res.scalar_one_or_none.return_value = integration

    db.execute.side_effect = [mock_delivery_res, mock_integ_res]

    with patch(
        "app.services.github_service.get_project_verification_status",
        return_value=(False, None),
    ):
        status_code, resp = await github_service.process_webhook_payload(
            db=db,
            delivery_id="delivery-unverified-456",
            event_type="pull_request",
            signature_header=sig,
            raw_body=raw_body,
        )

        assert status_code == 200
        assert resp.status == "skipped"
        assert "Domain unverified" in resp.message
        assert db.add.called


@pytest.mark.asyncio
async def test_execute_test_pr_review_blocks_unverified_domain() -> None:
    """Verify that on-demand test PR review raises PolicyViolationError if domain is unverified."""
    db = AsyncMock()
    project_id = uuid.uuid4()
    user_id = uuid.uuid4()

    project = Project(id=project_id, owner_id=user_id, name="Test App", base_domain="example.com")
    integration = GitHubIntegration(
        id=uuid.uuid4(),
        project_id=project_id,
        repo_owner="test-owner",
        repo_name="test-repo",
        webhook_secret="whsec_123",
        enabled=True,
        created_by=user_id,
    )

    mock_proj_res = MagicMock()
    mock_proj_res.scalar_one_or_none.return_value = project

    mock_integ_res = MagicMock()
    mock_integ_res.scalar_one_or_none.return_value = integration

    db.execute.side_effect = [mock_proj_res, mock_integ_res]

    with patch(
        "app.services.github_service.get_project_verification_status",
        return_value=(False, None),
    ):
        with pytest.raises(PolicyViolationError) as exc_info:
            await github_service.execute_test_pr_review(
                db=db,
                project_id=project_id,
                user_id=user_id,
                req=TestReviewRequest(pr_number=5, pr_title="Test PR"),
            )

        assert "Project domain is not verified" in str(exc_info.value)
