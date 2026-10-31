"""Unit tests verifying error handling, exception schemas, and lack of traceback leaks."""

import pytest
from fastapi import APIRouter
from httpx import ASGITransport, AsyncClient

from app.config import Settings
from app.core.errors import NotFoundError, PolicyViolationError
from app.main import create_app

# Router providing controlled test errors
error_router = APIRouter(prefix="/test-errors")


@error_router.get("/not-found")
async def trigger_not_found() -> None:
    raise NotFoundError("Test item was not found", details={"item_id": "123"})


@error_router.get("/policy-violation")
async def trigger_policy_violation() -> None:
    raise PolicyViolationError(
        "Private IP scanning is prohibited",
        code="SSRF_TARGET_BLOCKED",
        details={"ip": "127.0.0.1"},
    )


@error_router.get("/unhandled")
async def trigger_unhandled() -> None:
    raise RuntimeError("Unexpected internal crash with sensitive /etc/passwd path")


@pytest.fixture
async def error_client(test_settings: Settings) -> AsyncClient:
    app = create_app(test_settings)
    app.include_router(error_router)
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


@pytest.mark.asyncio
async def test_not_found_error_envelope(error_client: AsyncClient) -> None:
    """Verify custom NotFoundError maps to standard error envelope."""
    response = await error_client.get("/test-errors/not-found")
    assert response.status_code == 404
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "NOT_FOUND"
    assert data["error"]["message"] == "Test item was not found"
    assert data["error"]["details"] == {"item_id": "123"}
    assert data["error"]["request_id"].startswith("req_")


@pytest.mark.asyncio
async def test_policy_violation_error_envelope(error_client: AsyncClient) -> None:
    """Verify PolicyViolationError returns 400 with machine-readable code."""
    response = await error_client.get("/test-errors/policy-violation")
    assert response.status_code == 400
    data = response.json()
    assert data["error"]["code"] == "SSRF_TARGET_BLOCKED"
    assert "Private IP scanning is prohibited" in data["error"]["message"]
    assert data["error"]["details"] == {"ip": "127.0.0.1"}


@pytest.mark.asyncio
async def test_unhandled_exception_sanitization(error_client: AsyncClient) -> None:
    """Verify unhandled 500 error hides tracebacks and internal sensitive text."""
    response = await error_client.get("/test-errors/unhandled")
    assert response.status_code == 500
    data = response.json()
    assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"
    # Must NOT leak internal traceback details or internal file paths
    assert "/etc/passwd" not in response.text
    assert "RuntimeError" not in response.text
    assert "Traceback" not in response.text
    assert data["error"]["request_id"].startswith("req_")
