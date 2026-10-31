"""Integration tests for project management, CRUD, and tenant isolation."""

import pytest
from httpx import AsyncClient


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


@pytest.mark.asyncio
async def test_create_project_success(async_client: AsyncClient) -> None:
    """Verify authenticated user can create a project with domain normalization."""
    _, token = await create_user_and_token(async_client, "creator@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "name": "Acme Marketing",
        "base_domain": "  ACME.COM.  ",
    }
    response = await async_client.post("/api/v1/projects", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()

    assert data["name"] == "Acme Marketing"
    assert data["base_domain"] == "acme.com"
    assert data["is_verified"] is False
    assert data["latest_verification"] is not None
    assert data["latest_verification"]["domain"] == "acme.com"
    assert data["latest_verification"]["record_name"] == "_accessguard-verification.acme.com"
    assert data["latest_verification"]["record_type"] == "TXT"
    assert data["latest_verification"]["expected_value"].startswith("accessguard-verification=")


@pytest.mark.asyncio
async def test_create_project_duplicate_name_rejected(async_client: AsyncClient) -> None:
    """Verify duplicate project name for the same user is rejected with 409."""
    _, token = await create_user_and_token(async_client, "dupmaster@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {"name": "Duplicate Project", "base_domain": "domain-one.com"}
    resp1 = await async_client.post("/api/v1/projects", json=payload, headers=headers)
    assert resp1.status_code == 201

    payload2 = {"name": "Duplicate Project", "base_domain": "domain-two.com"}
    resp2 = await async_client.post("/api/v1/projects", json=payload2, headers=headers)
    assert resp2.status_code == 409
    assert resp2.json()["error"]["code"] == "CONFLICT"


@pytest.mark.asyncio
async def test_create_project_invalid_domain_rejected(async_client: AsyncClient) -> None:
    """Verify invalid domain syntax (e.g. URL scheme or path) is rejected with 422."""
    _, token = await create_user_and_token(async_client, "invalid.domain@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {"name": "Bad Project", "base_domain": "https://example.com/some/path"}
    response = await async_client.post("/api/v1/projects", json=payload, headers=headers)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_list_projects_tenant_isolation(async_client: AsyncClient) -> None:
    """Verify listing projects only returns projects owned by authenticated user."""
    _, token_alice = await create_user_and_token(async_client, "alice@example.com")
    _, token_bob = await create_user_and_token(async_client, "bob@example.com")

    headers_alice = {"Authorization": f"Bearer {token_alice}"}
    headers_bob = {"Authorization": f"Bearer {token_bob}"}

    # Alice creates 2 projects
    await async_client.post(
        "/api/v1/projects",
        json={"name": "Alice App 1", "base_domain": "alice1.org"},
        headers=headers_alice,
    )
    await async_client.post(
        "/api/v1/projects",
        json={"name": "Alice App 2", "base_domain": "alice2.org"},
        headers=headers_alice,
    )

    # Bob creates 1 project
    await async_client.post(
        "/api/v1/projects",
        json={"name": "Bob Portal", "base_domain": "bob.org"},
        headers=headers_bob,
    )

    # Alice lists projects
    resp_alice = await async_client.get("/api/v1/projects", headers=headers_alice)
    assert resp_alice.status_code == 200
    alice_data = resp_alice.json()
    assert alice_data["total"] == 2
    assert all(item["name"].startswith("Alice") for item in alice_data["items"])

    # Bob lists projects
    resp_bob = await async_client.get("/api/v1/projects", headers=headers_bob)
    assert resp_bob.status_code == 200
    bob_data = resp_bob.json()
    assert bob_data["total"] == 1
    assert bob_data["items"][0]["name"] == "Bob Portal"


@pytest.mark.asyncio
async def test_get_and_update_project(async_client: AsyncClient) -> None:
    """Verify retrieving and updating project metadata."""
    _, token = await create_user_and_token(async_client, "updater@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = await async_client.post(
        "/api/v1/projects",
        json={"name": "Initial Name", "base_domain": "updater.com"},
        headers=headers,
    )
    project_id = create_resp.json()["id"]

    # Get project
    get_resp = await async_client.get(f"/api/v1/projects/{project_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == "Initial Name"

    # Update project name
    patch_resp = await async_client.patch(
        f"/api/v1/projects/{project_id}",
        json={"name": "Updated Name"},
        headers=headers,
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["name"] == "Updated Name"


@pytest.mark.asyncio
async def test_idor_protection_cross_tenant_access_rejected(async_client: AsyncClient) -> None:
    """Verify User B cannot access, update, or archive User A's project (returns 404)."""
    _, token_alice = await create_user_and_token(async_client, "owner_alice@example.com")
    _, token_mallory = await create_user_and_token(async_client, "mallory@example.com")

    headers_alice = {"Authorization": f"Bearer {token_alice}"}
    headers_mallory = {"Authorization": f"Bearer {token_mallory}"}

    create_resp = await async_client.post(
        "/api/v1/projects",
        json={"name": "Confidential Project", "base_domain": "confidential.io"},
        headers=headers_alice,
    )
    project_id = create_resp.json()["id"]

    # Mallory attempts to GET Alice's project -> 404
    get_resp = await async_client.get(f"/api/v1/projects/{project_id}", headers=headers_mallory)
    assert get_resp.status_code == 404
    assert get_resp.json()["error"]["code"] == "NOT_FOUND"

    # Mallory attempts to PATCH Alice's project -> 404
    patch_resp = await async_client.patch(
        f"/api/v1/projects/{project_id}",
        json={"name": "Compromised Name"},
        headers=headers_mallory,
    )
    assert patch_resp.status_code == 404

    # Mallory attempts to DELETE Alice's project -> 404
    del_resp = await async_client.delete(f"/api/v1/projects/{project_id}", headers=headers_mallory)
    assert del_resp.status_code == 404


@pytest.mark.asyncio
async def test_archive_project_excludes_from_list(async_client: AsyncClient) -> None:
    """Verify archived project is soft-deleted and omitted from subsequent listing."""
    _, token = await create_user_and_token(async_client, "archiver@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = await async_client.post(
        "/api/v1/projects",
        json={"name": "To Archive", "base_domain": "archive-test.com"},
        headers=headers,
    )
    project_id = create_resp.json()["id"]

    # Archive
    del_resp = await async_client.delete(f"/api/v1/projects/{project_id}", headers=headers)
    assert del_resp.status_code == 204

    # List projects -> should be empty
    list_resp = await async_client.get("/api/v1/projects", headers=headers)
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] == 0

    # Direct GET on archived project returns 404
    get_resp = await async_client.get(f"/api/v1/projects/{project_id}", headers=headers)
    assert get_resp.status_code == 404
