"""Unit tests for liveness and readiness health endpoints."""

import pytest
from httpx import AsyncClient

from app.api.v1.health import DependencyCheck


@pytest.mark.asyncio
async def test_health_live_endpoint(async_client: AsyncClient) -> None:
    """Verify /health/live returns HTTP 200 with status alive."""
    response = await async_client.get("/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"


@pytest.mark.asyncio
async def test_api_v1_health_live_endpoint(async_client: AsyncClient) -> None:
    """Verify /api/v1/health/live responds correctly via versioned router."""
    response = await async_client.get("/api/v1/health/live")
    assert response.status_code == 200
    assert response.json()["status"] == "alive"


@pytest.mark.asyncio
async def test_health_ready_all_ok(
    async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify /health/ready returns HTTP 200 when all dependency probes pass."""
    async def mock_ok_redis(_url: str, _timeout: float = 2.0) -> DependencyCheck:
        return DependencyCheck(status="ok")

    async def mock_ok_qdrant(_url: str, _timeout: float = 2.0) -> DependencyCheck:
        return DependencyCheck(status="ok")

    monkeypatch.setattr("app.api.v1.health.probe_redis", mock_ok_redis)
    monkeypatch.setattr("app.api.v1.health.probe_qdrant", mock_ok_qdrant)

    response = await async_client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert "checks" in data
    # Database is NOT mocked: it actually executed `SELECT 1` on the async database session!
    assert data["checks"]["database"]["status"] == "ok"
    assert data["checks"]["redis"]["status"] == "ok"
    assert data["checks"]["qdrant"]["status"] == "ok"


@pytest.mark.asyncio
async def test_health_ready_unhealthy_dependency(
    async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify /health/ready returns HTTP 503 when a downstream dependency fails."""
    async def mock_failing_postgres(_db: object, _timeout: float = 2.0) -> DependencyCheck:
        return DependencyCheck(status="unhealthy", message="Database connectivity check failed")

    async def mock_ok_redis(_url: str, _timeout: float = 2.0) -> DependencyCheck:
        return DependencyCheck(status="ok")

    async def mock_ok_qdrant(_url: str, _timeout: float = 2.0) -> DependencyCheck:
        return DependencyCheck(status="ok")

    monkeypatch.setattr("app.api.v1.health.probe_postgres", mock_failing_postgres)
    monkeypatch.setattr("app.api.v1.health.probe_redis", mock_ok_redis)
    monkeypatch.setattr("app.api.v1.health.probe_qdrant", mock_ok_qdrant)

    response = await async_client.get("/health/ready")
    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "unready"
    assert data["checks"]["database"]["status"] == "unhealthy"
    assert data["checks"]["database"]["message"] == "Database connectivity check failed"


@pytest.mark.asyncio
async def test_probe_postgres_real_session(db_session: object) -> None:
    """Verify probe_postgres executes real async SELECT 1 on the database session."""
    from app.api.v1.health import probe_postgres
    res = await probe_postgres(db_session)
    assert res.status == "ok"
    assert res.message is None


@pytest.mark.asyncio
async def test_probe_redis_unreachable_network() -> None:
    """Verify probe_redis returns unhealthy without leaking connection credentials when host is unreachable."""
    from app.api.v1.health import probe_redis
    res = await probe_redis("redis://127.0.0.1:64799/0", timeout=0.5)
    assert res.status == "unhealthy"
    assert "password" not in (res.message or "").lower()
    assert res.message in ("Redis connection timed out", "Redis connectivity check failed")
