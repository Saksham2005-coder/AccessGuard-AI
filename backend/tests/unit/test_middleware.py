"""Unit tests for Request ID and CORS middleware."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_request_id_generated_automatically(async_client: AsyncClient) -> None:
    """Verify responses include an auto-generated X-Request-ID header."""
    response = await async_client.get("/health/live")
    assert response.status_code == 200
    assert "x-request-id" in response.headers
    assert response.headers["x-request-id"].startswith("req_")


@pytest.mark.asyncio
async def test_inbound_request_id_propagated(async_client: AsyncClient) -> None:
    """Verify client-supplied X-Request-ID is preserved and echoed."""
    custom_id = "req_custom_trace_98765"
    response = await async_client.get("/health/live", headers={"X-Request-ID": custom_id})
    assert response.status_code == 200
    assert response.headers["x-request-id"] == custom_id


@pytest.mark.asyncio
async def test_cors_allowed_origin(async_client: AsyncClient) -> None:
    """Verify configured origin receives access-control headers."""
    response = await async_client.get(
        "/health/live",
        headers={"Origin": "http://localhost:5173"},
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert response.headers.get("access-control-allow-credentials") == "true"


@pytest.mark.asyncio
async def test_cors_unauthorized_origin_rejected(async_client: AsyncClient) -> None:
    """Verify unauthorized origin does not receive access-control headers."""
    response = await async_client.get(
        "/health/live",
        headers={"Origin": "https://malicious-external-site.com"},
    )
    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers
