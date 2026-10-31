"""Integration tests for remediation proposals, human approval gates, and authorization."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.factory import set_cached_provider
from app.ai.mock_provider import MockLLMProvider
from app.db.models.finding import Finding
from app.db.models.project import Project
from app.db.models.scan import Scan
from app.db.models.scan_page import ScanPage


@pytest.fixture(autouse=True)
def mock_llm_for_tests():
    """Ensure fast, deterministic mock model is used for all API remediation tests."""
    set_cached_provider(MockLLMProvider())
    yield
    set_cached_provider(None)


async def create_user_and_token(
    client: AsyncClient, email: str, password: str = "SecurePass123!"
) -> tuple[dict, str]:
    """Helper to register and login a test user, returning (user_dict, access_token)."""
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "display_name": email.split("@")[0]},
    )
    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    data = login_resp.json()
    return data["user"], data["access_token"]


async def create_test_finding(
    db: AsyncSession,
    owner_id: uuid.UUID,
    rule_id: str = "image-alt",
) -> uuid.UUID:
    """Helper to persist a project, scan, scan_page, and finding owned by owner_id."""
    project = Project(
        owner_id=owner_id,
        name=f"Project-{uuid.uuid4().hex[:6]}",
        base_domain="example.org",
    )
    db.add(project)
    await db.flush()

    scan = Scan(
        project_id=project.id,
        requested_by=owner_id,
        target_url="https://example.org",
        status="completed",
        config={"max_pages": 1, "max_depth": 1},
    )
    db.add(scan)
    await db.flush()

    page = ScanPage(
        scan_id=scan.id,
        url="https://example.org/home",
        normalized_url="https://example.org/home",
        http_status=200,
        audit_status="completed",
    )
    db.add(page)
    await db.flush()

    finding = Finding(
        scan_page_id=page.id,
        axe_rule_id=rule_id,
        impact="critical",
        description="Images must have alternate text",
        help="Provide alt text for all non-decorative images",
        help_url="https://dequeuniversity.com/rules/axe/4.14/image-alt",
        wcag_tags=["wcag2a", "wcag111"],
        selector="img.hero",
        html_snippet='<img src="hero.jpg" class="hero">',
        failure_summary="Fix all of the following: Element does not have an alt attribute",
        fingerprint=f"fp-{uuid.uuid4().hex}",
        is_incomplete=False,
    )
    db.add(finding)
    await db.commit()
    await db.refresh(finding)
    return finding.id


@pytest.mark.asyncio
async def test_generate_and_get_remediation(
    async_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Verify owner can generate and retrieve an AI remediation proposal."""
    user, token = await create_user_and_token(async_client, "owner1@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    finding_id = await create_test_finding(db_session, uuid.UUID(user["id"]))

    # 1. Generate proposal
    post_resp = await async_client.post(
        f"/api/v1/findings/{finding_id}/remediations",
        headers=headers,
    )
    assert post_resp.status_code == 201
    post_data = post_resp.json()
    remediation_id = post_data["id"]

    assert post_data["finding_id"] == str(finding_id)
    assert post_data["status"] == "proposed"
    assert "alt" in post_data["recommendation"].lower()
    assert post_data["patch_format"] in ("snippet", "dom_operations")

    # 2. Retrieve proposal
    get_resp = await async_client.get(
        f"/api/v1/remediations/{remediation_id}",
        headers=headers,
    )
    assert get_resp.status_code == 200
    get_data = get_resp.json()
    assert get_data["id"] == remediation_id
    assert get_data["status"] == "proposed"


@pytest.mark.asyncio
async def test_non_owner_cannot_access_or_approve_remediation(
    async_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Verify non-owners are forbidden from viewing or deciding remediations."""
    owner, owner_token = await create_user_and_token(async_client, "owner2@example.com")
    intruder, intruder_token = await create_user_and_token(async_client, "intruder@example.com")
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    intruder_headers = {"Authorization": f"Bearer {intruder_token}"}

    finding_id = await create_test_finding(db_session, uuid.UUID(owner["id"]))

    # Owner creates remediation
    gen_resp = await async_client.post(
        f"/api/v1/findings/{finding_id}/remediations",
        headers=owner_headers,
    )
    assert gen_resp.status_code == 201
    remediation_id = gen_resp.json()["id"]

    # Intruder tries to get remediation
    intruder_get = await async_client.get(
        f"/api/v1/remediations/{remediation_id}",
        headers=intruder_headers,
    )
    assert intruder_get.status_code == 403
    assert intruder_get.json()["error"]["code"] == "FORBIDDEN"

    # Intruder tries to approve remediation
    intruder_approve = await async_client.post(
        f"/api/v1/remediations/{remediation_id}/approve",
        headers=intruder_headers,
        json={"decision": "approved", "comments": "Malicious approval"},
    )
    assert intruder_approve.status_code == 403
    assert intruder_approve.json()["error"]["code"] == "FORBIDDEN"


@pytest.mark.asyncio
async def test_approve_remediation_and_conflict_handling(
    async_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Verify owner can approve remediation and duplicate decisions return 409 Conflict."""
    owner, token = await create_user_and_token(async_client, "approver@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    finding_id = await create_test_finding(db_session, uuid.UUID(owner["id"]))

    gen_resp = await async_client.post(
        f"/api/v1/findings/{finding_id}/remediations",
        headers=headers,
    )
    assert gen_resp.status_code == 201
    remediation_id = gen_resp.json()["id"]

    # Approve remediation
    app_resp = await async_client.post(
        f"/api/v1/remediations/{remediation_id}/approve",
        headers=headers,
        json={"decision": "approved", "comments": "Reviewed and safe for snapshot test"},
    )
    assert app_resp.status_code == 200
    app_data = app_resp.json()
    assert app_data["status"] == "validated"
    assert len(app_data["approvals"]) == 1
    assert app_data["approvals"][0]["decision"] == "approved"
    assert app_data["approvals"][0]["comments"] == "Reviewed and safe for snapshot test"
    assert len(app_data["validation_results"]) >= 1
    assert app_data["validation_results"][0]["passed"] is True

    # Duplicate decision must raise 409 Conflict
    dup_resp = await async_client.post(
        f"/api/v1/remediations/{remediation_id}/approve",
        headers=headers,
        json={"decision": "approved", "comments": "Duplicate approval attempt"},
    )
    assert dup_resp.status_code == 409
    assert dup_resp.json()["error"]["code"] == "CONFLICT"


@pytest.mark.asyncio
async def test_reject_remediation(
    async_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Verify owner can reject a remediation proposal with reviewer comments."""
    owner, token = await create_user_and_token(async_client, "rejector@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    finding_id = await create_test_finding(db_session, uuid.UUID(owner["id"]))

    gen_resp = await async_client.post(
        f"/api/v1/findings/{finding_id}/remediations",
        headers=headers,
    )
    assert gen_resp.status_code == 201
    remediation_id = gen_resp.json()["id"]

    # Reject remediation
    rej_resp = await async_client.post(
        f"/api/v1/remediations/{remediation_id}/reject",
        headers=headers,
        json={"decision": "rejected", "comments": "Proposed alt text is too generic"},
    )
    assert rej_resp.status_code == 200
    rej_data = rej_resp.json()
    assert rej_data["status"] == "rejected"
    assert len(rej_data["approvals"]) == 1
    assert rej_data["approvals"][0]["decision"] == "rejected"
    assert rej_data["approvals"][0]["comments"] == "Proposed alt text is too generic"

    # Further validation or approval is blocked with 409 Conflict
    conflict_resp = await async_client.post(
        f"/api/v1/remediations/{remediation_id}/reject",
        headers=headers,
        json={"decision": "rejected"},
    )
    assert conflict_resp.status_code == 409
