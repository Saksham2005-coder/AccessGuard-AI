"""System-wide security verification covering IDOR boundaries, SSRF policies, and safe patch constraints."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.schemas import PatchOperation
from app.db.models.finding import Finding
from app.db.models.project import Project
from app.db.models.remediation import Remediation
from app.db.models.scan import Scan
from app.db.models.scan_page import ScanPage
from app.scanner.target_policy import classify_ip_address


async def register_and_get_token(client: AsyncClient, email: str) -> str:
    """Helper to register and login a test user."""
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "SecurePassword123!",
            "display_name": email.split("@")[0],
        },
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "SecurePassword123!"},
    )
    return login_resp.json()["access_token"]


@pytest.mark.asyncio
async def test_remediation_idor_tenant_boundary(
    async_client: AsyncClient, db_session: AsyncSession
) -> None:
    """Verify that User B cannot access, approve, or reject User A's remediation proposals."""
    # User A creates a project and remediation
    token_a = await register_and_get_token(async_client, "user_a@example.com")
    token_b = await register_and_get_token(async_client, "user_b@example.com")

    # Get User A's ID
    me_resp = await async_client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {token_a}"}
    )
    user_a_id = uuid.UUID(me_resp.json()["id"])

    proj_a = Project(
        owner_id=user_a_id,
        name="User A App",
        base_domain="usera.com",
    )
    db_session.add(proj_a)
    await db_session.flush()

    scan_a = Scan(
        project_id=proj_a.id,
        requested_by=user_a_id,
        target_url="https://usera.com",
        status="completed",
        config={},
    )
    db_session.add(scan_a)
    await db_session.flush()

    scan_page_a = ScanPage(
        scan_id=scan_a.id,
        url="https://usera.com",
        normalized_url="https://usera.com",
        http_status=200,
        audit_status="completed",
    )
    db_session.add(scan_page_a)
    await db_session.flush()

    finding_a = Finding(
        scan_page_id=scan_page_a.id,
        axe_rule_id="image-alt",
        description="Missing alt",
        fingerprint="fp_user_a_finding",
        is_incomplete=False,
    )
    db_session.add(finding_a)
    await db_session.flush()

    rem_a = Remediation(
        finding_id=finding_a.id,
        status="pending_approval",
        root_cause="Missing alt text",
        recommendation="Add alt",
        patch_format="safe_dom_patch",
        patch_payload={"selector": "img", "operations": []},
        before_snippet="<img src='logo.png'>",
        after_snippet="<img src='logo.png' alt='Logo'>",
    )
    db_session.add(rem_a)
    await db_session.commit()

    # User B attempts to access User A's remediation listing
    list_b_resp = await async_client.get(
        f"/api/v1/remediations?finding_id={finding_a.id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert list_b_resp.status_code == 200
    # Must be empty because User B does not own User A's project
    assert len(list_b_resp.json()) == 0

    # User B attempts to approve User A's remediation
    approve_b_resp = await async_client.post(
        f"/api/v1/remediations/{rem_a.id}/approve",
        json={"decision": "approved", "comments": "Malicious approval attempt"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    # Must fail with 403 Forbidden or 404 Not Found
    assert approve_b_resp.status_code in (403, 404)

    # User B attempts to reject User A's remediation
    reject_b_resp = await async_client.post(
        f"/api/v1/remediations/{rem_a.id}/reject",
        json={"decision": "rejected", "comments": "Malicious rejection attempt"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert reject_b_resp.status_code in (403, 404)


def test_ssrf_egress_hardening_policies() -> None:
    """Verify that SSRF target policy blocks private, loopback, and metadata destinations."""
    # Private RFC 1918 IPv4
    is_safe, _ = classify_ip_address("10.0.0.1", allow_loopback=False)
    assert not is_safe
    is_safe, _ = classify_ip_address("172.16.0.1", allow_loopback=False)
    assert not is_safe
    is_safe, _ = classify_ip_address("192.168.1.1", allow_loopback=False)
    assert not is_safe

    # Loopback IPv4 and IPv6
    is_safe, _ = classify_ip_address("127.0.0.1", allow_loopback=False)
    assert not is_safe
    is_safe, _ = classify_ip_address("::1", allow_loopback=False)
    assert not is_safe

    # Cloud Instance Metadata Service (AWS/GCP/Azure)
    is_safe, _ = classify_ip_address("169.254.169.254", allow_loopback=False)
    assert not is_safe

    # Public Routable IP
    is_safe, _ = classify_ip_address("93.184.216.34", allow_loopback=False)
    assert is_safe


def test_safe_patch_policy_rejects_arbitrary_code() -> None:
    """Verify that safe DOM patch policy strictly prevents execution vectors."""
    # Allowed accessible attribute
    op_valid = PatchOperation(
        operation="set_attribute",
        selector="img",
        attribute="alt",
        value="Accessible image description",
    )
    assert op_valid.attribute == "alt"

    # Blocked event handler attributes
    for forbidden_attr in ["onclick", "onload", "onerror", "style", "src", "href"]:
        with pytest.raises(ValueError) as exc:
            PatchOperation(
                operation="set_attribute",
                selector="img",
                attribute=forbidden_attr,
                value="action",
            )
        assert "prohibited" in str(exc.value) or "not in the allowlist" in str(exc.value)

    # Blocked URI schemes in attribute values
    for forbidden_val in ["javascript:alert(1)", "vbscript:msgbox(1)"]:
        with pytest.raises(ValueError) as exc:
            PatchOperation(
                operation="set_attribute",
                selector="img",
                attribute="alt",
                value=forbidden_val,
            )
        assert "forbidden" in str(exc.value)
