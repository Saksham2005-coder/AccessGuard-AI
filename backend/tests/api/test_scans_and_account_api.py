"""Integration tests for scan creation status rules and user profile / password mutations."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.project import Project


async def create_user_and_token(
    client: AsyncClient, email: str, password: str = "SecurePass123!"
) -> tuple[dict, str]:
    """Helper to register and login a test user, returning (user_dict, access_token)."""
    reg_resp = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "display_name": email.split("@")[0]},
    )
    assert reg_resp.status_code == 201

    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login_resp.status_code == 200
    data = login_resp.json()
    return data["user"], data["access_token"]


@pytest.mark.asyncio
async def test_create_scan_on_unverified_project_returns_403(async_client: AsyncClient) -> None:
    """BUG-04 regression: creating a scan on an unverified project must return 403 Forbidden."""
    _, token = await create_user_and_token(async_client, "user_scan_unverified@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Create unverified project
    proj_resp = await async_client.post(
        "/api/v1/projects",
        json={"name": "Unverified Site", "base_domain": "unverified.example.org"},
        headers=headers,
    )
    assert proj_resp.status_code == 201
    project_id = proj_resp.json()["id"]

    # Attempt to start scan on unverified project
    scan_resp = await async_client.post(
        f"/api/v1/projects/{project_id}/scans",
        json={"target_url": "https://unverified.example.org", "max_pages": 5, "max_depth": 1},
        headers=headers,
    )
    assert scan_resp.status_code == 403
    error_data = scan_resp.json()
    assert "not verified" in error_data["error"]["message"].lower()


@pytest.mark.asyncio
async def test_create_scan_on_nonexistent_project_returns_404(async_client: AsyncClient) -> None:
    """Attempting scan on non-existent project returns 404 Not Found."""
    _, token = await create_user_and_token(async_client, "user_scan_404@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    random_id = uuid.uuid4()
    scan_resp = await async_client.post(
        f"/api/v1/projects/{random_id}/scans",
        json={"target_url": "https://example.org", "max_pages": 5, "max_depth": 1},
        headers=headers,
    )
    assert scan_resp.status_code == 404


@pytest.mark.asyncio
async def test_create_scan_on_other_tenant_project_returns_404(
    async_client: AsyncClient, db_session: AsyncSession
) -> None:
    """Tenant isolation: scanning another tenant's project returns 404 (non-disclosure)."""
    user_a, _ = await create_user_and_token(async_client, "tenant_a_scan@example.com")
    _, token_b = await create_user_and_token(async_client, "tenant_b_scan@example.com")
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Project owned by User A
    project = Project(
        owner_id=uuid.UUID(user_a["id"]),
        name="Tenant A Project",
        base_domain="tenant-a.com",
    )
    db_session.add(project)
    await db_session.commit()

    # User B attempts to scan User A's project
    scan_resp = await async_client.post(
        f"/api/v1/projects/{project.id}/scans",
        json={"target_url": "https://tenant-a.com", "max_pages": 5, "max_depth": 1},
        headers=headers_b,
    )
    assert scan_resp.status_code == 404


@pytest.mark.asyncio
async def test_update_user_profile(async_client: AsyncClient) -> None:
    """PATCH /api/v1/auth/me updates display_name and returns updated profile."""
    _, token = await create_user_and_token(async_client, "update_profile@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    update_resp = await async_client.patch(
        "/api/v1/auth/me",
        json={"display_name": "Jane Lead Auditor"},
        headers=headers,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["display_name"] == "Jane Lead Auditor"

    # Verify GET /me reflects change
    me_resp = await async_client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["display_name"] == "Jane Lead Auditor"


@pytest.mark.asyncio
async def test_change_password_flow(async_client: AsyncClient) -> None:
    """POST /api/v1/auth/change-password changes password and rejects old credentials."""
    email = "change_pass@example.com"
    old_pass = "OldPassword123!"
    new_pass = "NewSuperSecurePass456!"

    _, token = await create_user_and_token(async_client, email, password=old_pass)
    headers = {"Authorization": f"Bearer {token}"}

    # Mismatched confirmation fails validation (422)
    bad_confirm = await async_client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": old_pass,
            "new_password": new_pass,
            "confirm_password": "DoesNotMatchPassword!",
        },
        headers=headers,
    )
    assert bad_confirm.status_code == 422

    # Wrong current password fails with 401
    wrong_current = await async_client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": "WrongPassword999!",
            "new_password": new_pass,
            "confirm_password": new_pass,
        },
        headers=headers,
    )
    assert wrong_current.status_code == 401

    # Valid change password succeeds
    success_resp = await async_client.post(
        "/api/v1/auth/change-password",
        json={
            "current_password": old_pass,
            "new_password": new_pass,
            "confirm_password": new_pass,
        },
        headers=headers,
    )
    assert success_resp.status_code == 200
    assert "successfully changed" in success_resp.json()["message"].lower()

    # Login with old password fails
    old_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": old_pass},
    )
    assert old_login.status_code == 401

    # Login with new password succeeds
    new_login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": new_pass},
    )
    assert new_login.status_code == 200
    assert "access_token" in new_login.json()
