"""Integration tests for user registration, authentication, token rotation, and session lifecycle."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_user_success(async_client: AsyncClient) -> None:
    """Verify registration creates user with normalized email and no password leak."""
    payload = {
        "email": "  Developer@Example.COM  ",
        "password": "SecurePassword123!",
        "display_name": "Lead Engineer",
    }
    response = await async_client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()

    assert data["email"] == "developer@example.com"
    assert data["display_name"] == "Lead Engineer"
    assert data["is_active"] is True
    assert "id" in data
    # Password and hash must never be returned
    assert "password" not in data
    assert "password_hash" not in data


@pytest.mark.asyncio
async def test_register_duplicate_email_rejected(async_client: AsyncClient) -> None:
    """Verify duplicate email registration is rejected with 409 Conflict."""
    payload = {
        "email": "duplicate@example.com",
        "password": "SecurePassword123!",
    }
    resp1 = await async_client.post("/api/v1/auth/register", json=payload)
    assert resp1.status_code == 201

    resp2 = await async_client.post("/api/v1/auth/register", json=payload)
    assert resp2.status_code == 409
    assert resp2.json()["error"]["code"] == "CONFLICT"


@pytest.mark.asyncio
async def test_register_short_password_rejected(async_client: AsyncClient) -> None:
    """Verify passwords shorter than 8 characters are rejected."""
    payload = {
        "email": "shortpass@example.com",
        "password": "short",
    }
    response = await async_client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_login_success_and_cookie(async_client: AsyncClient) -> None:
    """Verify login authenticates credentials, returns JWT, and attaches refresh cookie."""
    # 1. Register user
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": "login.user@example.com", "password": "MySecretPassword123!"},
    )

    # 2. Login
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "LOGIN.USER@example.com", "password": "MySecretPassword123!"},
    )
    assert login_resp.status_code == 200
    login_data = login_resp.json()

    assert "access_token" in login_data
    assert login_data["token_type"] == "bearer"
    assert login_data["user"]["email"] == "login.user@example.com"

    # Refresh cookie should be present
    assert "accessguard_refresh_token" in login_resp.cookies


@pytest.mark.asyncio
async def test_login_invalid_password_rejected(async_client: AsyncClient) -> None:
    """Verify login with incorrect password returns 401."""
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": "alice@example.com", "password": "CorrectPassword123!"},
    )

    response = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "alice@example.com", "password": "IncorrectPassword!"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_FAILED"


@pytest.mark.asyncio
async def test_refresh_token_rotation(async_client: AsyncClient) -> None:
    """Verify refresh token rotates session and invalidates previous token."""
    # 1. Register & login
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": "rotator@example.com", "password": "SecurePassword123!"},
    )
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "rotator@example.com", "password": "SecurePassword123!"},
    )
    initial_cookie = login_resp.cookies.get("accessguard_refresh_token")
    assert initial_cookie is not None

    # 2. Refresh session using cookie
    refresh_resp = await async_client.post("/api/v1/auth/refresh")
    assert refresh_resp.status_code == 200
    rotated_cookie = refresh_resp.cookies.get("accessguard_refresh_token")
    assert rotated_cookie is not None
    assert rotated_cookie != initial_cookie

    # 3. Old refresh token must be rejected (replay prevention)
    replay_client = AsyncClient(
        transport=async_client._transport,
        base_url="http://testserver",
        cookies={"accessguard_refresh_token": initial_cookie},
    )
    replay_resp = await replay_client.post("/api/v1/auth/refresh")
    assert replay_resp.status_code == 401


@pytest.mark.asyncio
async def test_logout_revokes_session(async_client: AsyncClient) -> None:
    """Verify logout revokes active refresh session and prevents subsequent refresh."""
    await async_client.post(
        "/api/v1/auth/register",
        json={"email": "logout.test@example.com", "password": "SecurePassword123!"},
    )
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "logout.test@example.com", "password": "SecurePassword123!"},
    )
    cookie_token = login_resp.cookies.get("accessguard_refresh_token")

    # Logout
    logout_resp = await async_client.post("/api/v1/auth/logout")
    assert logout_resp.status_code == 200

    # Refresh attempt with revoked cookie fails
    refresh_client = AsyncClient(
        transport=async_client._transport,
        base_url="http://testserver",
        cookies={"accessguard_refresh_token": cookie_token},
    )
    subsequent_refresh = await refresh_client.post("/api/v1/auth/refresh")
    assert subsequent_refresh.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_profile(async_client: AsyncClient) -> None:
    """Verify /auth/me returns authenticated user with valid Bearer token."""
    # 1. Register & login
    await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "me.check@example.com",
            "password": "SecurePassword123!",
            "display_name": "Me User",
        },
    )
    login_resp = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "me.check@example.com", "password": "SecurePassword123!"},
    )
    access_token = login_resp.json()["access_token"]

    # 2. Access /auth/me with Bearer token
    me_resp = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["email"] == "me.check@example.com"
    assert me_data["display_name"] == "Me User"

    # 3. Access without token fails
    unauth_resp = await async_client.get("/api/v1/auth/me")
    assert unauth_resp.status_code == 401
