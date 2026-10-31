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
async def test_health_ready_all_ok(async_client: AsyncClient) -> None:
    """Verify /health/ready returns HTTP 200 when all dependency probes pass."""
    response = await async_client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert "checks" in data
    assert data["checks"]["database"]["status"] == "ok"
    assert data["checks"]["redis"]["status"] == "ok"
    assert data["checks"]["qdrant"]["status"] == "ok"


@pytest.mark.asyncio
async def test_health_ready_unhealthy_dependency(
    async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify /health/ready returns HTTP 503 when a downstream dependency fails."""

    async def mock_failing_postgres(_url: str, _timeout: float = 2.0) -> DependencyCheck:
        return DependencyCheck(status="unhealthy", message="Connection refused")

    monkeypatch.setattr("app.api.v1.health.probe_postgres", mock_failing_postgres)

    response = await async_client.get("/health/ready")
    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "unready"
    assert data["checks"]["database"]["status"] == "unhealthy"
    assert data["checks"]["database"]["message"] == "Connection refused"
