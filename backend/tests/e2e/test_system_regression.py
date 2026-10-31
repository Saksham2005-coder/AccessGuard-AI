"""End-to-end full system regression test suite for AccessGuard AI."""

import uuid
from unittest.mock import patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.finding import Finding
from app.db.models.project import Project
from app.db.models.remediation import Remediation
from app.db.models.scan import Scan
from app.db.models.scan_page import ScanPage


async def get_auth_token(client: AsyncClient, email: str) -> str:
    """Helper to register and login a test user, returning access_token."""
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "SecurePassword123!", "display_name": "E2E Tester"},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "SecurePassword123!"},
    )
    return login_resp.json()["access_token"]


@pytest.mark.asyncio
async def test_full_system_regression_lifecycle(
    async_client: AsyncClient, db_session: AsyncSession
) -> None:
    """Validate full product user journey from auth, projects, findings, AI remediation to snapshot validation."""
    # 1. Authenticate user
    token = await get_auth_token(async_client, "regression.user@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Project
    proj_resp = await async_client.post(
        "/api/v1/projects",
        json={"name": "Acme Portal", "base_domain": "portal.acme.com"},
        headers=headers,
    )
    assert proj_resp.status_code == 201
    proj_data = proj_resp.json()
    project_id = proj_data["id"]
    assert proj_data["base_domain"] == "portal.acme.com"
    assert proj_data["is_verified"] is False

    # 3. Simulate verified domain control via DNS TXT verification endpoint
    from app.services.verification_service import set_dns_resolver_override

    expected_txt = proj_data["latest_verification"]["expected_value"]
    record_name = proj_data["latest_verification"]["record_name"]

    async def mock_resolver(domain: str) -> list[str]:
        if domain == record_name:
            return [expected_txt]
        return []

    set_dns_resolver_override(mock_resolver)

    check_resp = await async_client.post(
        f"/api/v1/projects/{project_id}/domain-verification/check",
        headers=headers,
    )
    assert check_resp.status_code == 200
    assert check_resp.json()["verified"] is True

    # 4. Create Scan & Persist deterministic findings fixture
    db_proj = await db_session.get(Project, uuid.UUID(project_id))
    assert db_proj is not None
    scan = Scan(
        project_id=uuid.UUID(project_id),
        requested_by=db_proj.owner_id,
        target_url="https://portal.acme.com",
        status="completed",
        config={"max_pages": 5, "max_depth": 2},
        total_pages=1,
        pages_succeeded=1,
        pages_failed=0,
        total_violations=1,
        axe_version="4.14.0",
        browser_version="Chromium 131",
    )
    db_session.add(scan)
    await db_session.flush()

    scan_page = ScanPage(
        scan_id=scan.id,
        url="https://portal.acme.com",
        normalized_url="https://portal.acme.com",
        http_status=200,
        audit_status="completed",
    )
    db_session.add(scan_page)
    await db_session.flush()

    finding = Finding(
        scan_page_id=scan_page.id,
        axe_rule_id="image-alt",
        impact="critical",
        description="Images must have alternate text",
        help="Elements must have an alt attribute",
        help_url="https://dequeuniversity.com/rules/axe/4.14/image-alt",
        selector="img",
        html_snippet="<img src='/hero.png'>",
        failure_summary="Fix any of the following: Element does not have an alt attribute",
        wcag_tags=["wcag2a", "wcag111"],
        fingerprint="fp_regression_hero_banner",
        is_incomplete=False,
    )
    db_session.add(finding)
    await db_session.commit()

    # 5. Query Findings via API with impact filter
    findings_resp = await async_client.get(
        f"/api/v1/findings?project_id={project_id}&impact=critical",
        headers=headers,
    )
    assert findings_resp.status_code == 200
    findings_data = findings_resp.json()
    assert findings_data["total"] == 1
    assert findings_data["items"][0]["axe_rule_id"] == "image-alt"
    finding_id = findings_data["items"][0]["id"]

    # 6. Generate AI Remediation Proposal
    remediation = Remediation(
        finding_id=uuid.UUID(finding_id),
        status="pending_approval",
        root_cause="Hero banner graphic lacks descriptive text equivalent for screen readers.",
        recommendation="Add an alt attribute with descriptive text summarizing the hero graphic.",
        patch_format="safe_dom_patch",
        patch_payload={
            "selector": "img",
            "operations": [
                {
                    "operation": "set_attribute",
                    "selector": "img",
                    "attribute": "alt",
                    "value": "Acme Portal Main Hero Presentation",
                }
            ],
        },
        before_snippet="<img src='/hero.png'>",
        after_snippet="<img src='/hero.png' alt='Acme Portal Main Hero Presentation'>",
        confidence=0.98,
        model_provider="mock",
        model_name="deterministic-mock",
        prompt_version="1.0.0",
    )
    db_session.add(remediation)
    await db_session.commit()

    # 7. List Remediations via API
    rem_list_resp = await async_client.get(
        f"/api/v1/remediations?finding_id={finding_id}",
        headers=headers,
    )
    assert rem_list_resp.status_code == 200
    rem_items = rem_list_resp.json()
    assert len(rem_items) == 1
    assert rem_items[0]["status"] == "pending_approval"
    rem_id = rem_items[0]["id"]

    # 8. Human Review Decision: Approve Proposal
    approve_resp = await async_client.post(
        f"/api/v1/remediations/{rem_id}/approve",
        json={"decision": "approved", "comments": "Verified alt text meets WCAG 1.1.1"},
        headers=headers,
    )
    assert approve_resp.status_code == 200
    approved_data = approve_resp.json()
    assert approved_data["status"] in ("approved", "validated")
    assert len(approved_data["approvals"]) >= 1
    assert any("WCAG 1.1.1" in str(appr.get("comments")) for appr in approved_data["approvals"])

    # 9. Verify or Trigger Isolated Snapshot Validation
    if approved_data["status"] == "validated":
        assert len(approved_data["validation_results"]) >= 1
        assert approved_data["validation_results"][0]["passed"] is True
    else:
        mock_axe_result = {
            "passed": True,
            "original_rule_resolved": True,
            "new_violations": [],
            "details": {"engine": "axe-core 4.14.0", "network_aborted": True},
        }
        with patch(
            "app.services.remediation_service.validate_snapshot_isolated",
            return_value=mock_axe_result,
        ):
            val_resp = await async_client.post(
                f"/api/v1/remediations/{rem_id}/validate",
                headers=headers,
            )
            assert val_resp.status_code == 200
            val_data = val_resp.json()
            assert val_data["status"] == "validated"
            assert len(val_data["validation_results"]) >= 1
            assert val_data["validation_results"][0]["passed"] is True
            assert val_data["validation_results"][0]["original_rule_resolved"] is True
