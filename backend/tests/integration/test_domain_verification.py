"""Integration tests for DNS TXT domain verification workflow."""

from collections.abc import Generator
from datetime import timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import utc_now
from app.db.models.domain_verification import ProjectDomainVerification
from app.services.verification_service import set_dns_resolver_override


@pytest.fixture(autouse=True)
def clean_dns_resolver() -> Generator[None, None, None]:
    """Ensure DNS resolver mock is reset after each test."""
    yield
    set_dns_resolver_override(None)


async def create_user_and_token(
    client: AsyncClient, email: str, password: str = "SecurePass123!"
) -> tuple[dict, str]:
    """Helper to register and login a test user."""
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
async def test_domain_verification_success(async_client: AsyncClient) -> None:
    """Verify domain verification check succeeds when DNS TXT record contains expected token."""
    _, token = await create_user_and_token(async_client, "dns.verifier@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create project
    create_resp = await async_client.post(
        "/api/v1/projects",
        json={"name": "DNS Test App", "base_domain": "verified.example.org"},
        headers=headers,
    )
    assert create_resp.status_code == 201
    project_data = create_resp.json()
    project_id = project_data["id"]
    expected_txt = project_data["latest_verification"]["expected_value"]
    record_name = project_data["latest_verification"]["record_name"]

    # 2. Inject mock DNS resolver returning the matching TXT record
    async def mock_resolver(domain: str) -> list[str]:
        if domain == record_name:
            return ["v=spf1 include:_spf.google.com ~all", expected_txt]
        return []

    set_dns_resolver_override(mock_resolver)

    # 3. Trigger verification check
    check_resp = await async_client.post(
        f"/api/v1/projects/{project_id}/domain-verification/check",
        headers=headers,
    )
    assert check_resp.status_code == 200
    check_data = check_resp.json()

    assert check_data["verified"] is True
    assert check_data["status"] == "verified"
    assert "Domain control verified successfully" in check_data["message"]
    assert check_data["verification"]["verified_at"] is not None

    # 4. Verify project representation now reports is_verified = True
    proj_resp = await async_client.get(f"/api/v1/projects/{project_id}", headers=headers)
    assert proj_resp.status_code == 200
    assert proj_resp.json()["is_verified"] is True


@pytest.mark.asyncio
async def test_domain_verification_mismatched_record(async_client: AsyncClient) -> None:
    """Verify check fails when TXT records exist but do not match expected token."""
    _, token = await create_user_and_token(async_client, "dns.mismatch@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = await async_client.post(
        "/api/v1/projects",
        json={"name": "Mismatch App", "base_domain": "mismatch.example.org"},
        headers=headers,
    )
    project_id = create_resp.json()["id"]

    # Mock resolver returning irrelevant TXT record
    async def mock_resolver(_domain: str) -> list[str]:
        return ["accessguard-verification=wrong-token-value"]

    set_dns_resolver_override(mock_resolver)

    check_resp = await async_client.post(
        f"/api/v1/projects/{project_id}/domain-verification/check",
        headers=headers,
    )
    assert check_resp.status_code == 200
    check_data = check_resp.json()

    assert check_data["verified"] is False
    assert check_data["status"] == "pending"
    assert "Verification TXT record not found" in check_data["message"]


@pytest.mark.asyncio
async def test_domain_verification_nxdomain(async_client: AsyncClient) -> None:
    """Verify check fails gracefully when DNS query yields no TXT records."""
    _, token = await create_user_and_token(async_client, "dns.nxdomain@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = await async_client.post(
        "/api/v1/projects",
        json={"name": "NX App", "base_domain": "nxdomain.example.org"},
        headers=headers,
    )
    project_id = create_resp.json()["id"]

    async def mock_resolver(_domain: str) -> list[str]:
        return []

    set_dns_resolver_override(mock_resolver)

    check_resp = await async_client.post(
        f"/api/v1/projects/{project_id}/domain-verification/check",
        headers=headers,
    )
    assert check_resp.status_code == 200
    check_data = check_resp.json()

    assert check_data["verified"] is False
    assert check_data["status"] == "pending"


@pytest.mark.asyncio
async def test_domain_verification_expired_token(
    async_client: AsyncClient, db_session: AsyncSession
) -> None:
    """Verify expired challenge token is marked expired and rejected."""
    _, token = await create_user_and_token(async_client, "dns.expired@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = await async_client.post(
        "/api/v1/projects",
        json={"name": "Expired App", "base_domain": "expired.example.org"},
        headers=headers,
    )
    project_id = create_resp.json()["id"]

    # Expire token in database
    past_time = utc_now() - timedelta(hours=1)
    await db_session.execute(
        update(ProjectDomainVerification)
        .where(ProjectDomainVerification.domain == "expired.example.org")
        .values(expires_at=past_time)
    )
    await db_session.commit()

    check_resp = await async_client.post(
        f"/api/v1/projects/{project_id}/domain-verification/check",
        headers=headers,
    )
    assert check_resp.status_code == 200
    check_data = check_resp.json()

    assert check_data["verified"] is False
    assert check_data["status"] == "expired"
    assert "expired" in check_data["message"].lower()


@pytest.mark.asyncio
async def test_regenerate_domain_verification_challenge(async_client: AsyncClient) -> None:
    """Verify endpoint to regenerate domain verification generates a new pending token."""
    _, token = await create_user_and_token(async_client, "dns.regen@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    create_resp = await async_client.post(
        "/api/v1/projects",
        json={"name": "Regen App", "base_domain": "regen.example.org"},
        headers=headers,
    )
    project_id = create_resp.json()["id"]
    token_1 = create_resp.json()["latest_verification"]["expected_value"]

    # Regenerate token
    regen_resp = await async_client.post(
        f"/api/v1/projects/{project_id}/domain-verification",
        headers=headers,
    )
    assert regen_resp.status_code == 201
    regen_data = regen_resp.json()
    token_2 = regen_data["expected_value"]

    assert token_2 != token_1
    assert regen_data["status"] == "pending"
