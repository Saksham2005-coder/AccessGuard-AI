"""Pytest global fixtures, test settings, and ASGI client configuration."""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_current_settings
from app.config import Settings
from app.main import create_app


@pytest.fixture
def test_settings() -> Settings:
    """Provide isolated Settings instance for test execution."""
    return Settings(
        APP_ENV="test",
        APP_NAME="AccessGuard AI Test",
        API_V1_PREFIX="/api/v1",
        FRONTEND_ORIGINS=["http://localhost:5173", "http://testserver"],
        DATABASE_URL="postgresql+psycopg://test:test@localhost:5432/accessguard_test",
        REDIS_URL="redis://localhost:6379/1",
        QDRANT_URL="http://localhost:6333",
        JWT_SECRET_KEY="test-secret-key-that-is-at-least-32-chars-long",
        LLM_PROVIDER="mock",
        TEST_ALLOW_LOOPBACK=True,
    )


@pytest.fixture
async def async_client(test_settings: Settings) -> AsyncGenerator[AsyncClient, None]:
    """Yield HTTPX AsyncClient configured with test application instance."""
    test_app = create_app(test_settings)
    test_app.dependency_overrides[get_current_settings] = lambda: test_settings

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
