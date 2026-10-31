"""Pytest global fixtures, test settings, and ASGI client configuration."""

from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.api.deps import get_current_settings, get_db_session
from app.config import Settings
from app.db.base import Base
from app.db.models import *  # noqa: F403
from app.db.models.user import User
from app.main import create_app
from app.schemas.auth import UserRegisterRequest
from app.services.auth_service import register_user


@pytest.fixture
def test_settings() -> Settings:
    """Provide isolated Settings instance for test execution."""
    return Settings(
        APP_ENV="test",
        APP_NAME="AccessGuard AI Test",
        API_V1_PREFIX="/api/v1",
        FRONTEND_ORIGINS=["http://localhost:5173", "http://testserver"],
        DATABASE_URL="sqlite+aiosqlite:///:memory:",
        REDIS_URL="redis://localhost:6379/1",
        QDRANT_URL="http://localhost:6333",
        JWT_SECRET_KEY="test-secret-key-that-is-at-least-32-chars-long",
        LLM_PROVIDER="mock",
        TEST_ALLOW_LOOPBACK=True,
    )


@pytest.fixture
async def test_engine() -> AsyncGenerator[AsyncEngine, None]:
    """Create in-memory SQLite async engine with all tables for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        future=True,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db_session(test_engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Yield an isolated AsyncSession bound to the in-memory test database."""
    session_factory = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with session_factory() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def async_client(
    test_settings: Settings, db_session: AsyncSession
) -> AsyncGenerator[AsyncClient, None]:
    """Yield HTTPX AsyncClient configured with test app and in-memory test database session."""
    test_app = create_app(test_settings)
    test_app.dependency_overrides[get_current_settings] = lambda: test_settings

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    test_app.dependency_overrides[get_db_session] = override_get_db

    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


@pytest.fixture
def user_factory(db_session: AsyncSession):
    """Factory creating and persisting test users."""

    async def _create_user(
        email: str = "test.user@example.com",
        password: str = "SecurePassword123!",
        display_name: str = "Test User",
    ) -> User:
        req = UserRegisterRequest(email=email, password=password, display_name=display_name)
        user = await register_user(db_session, req)
        await db_session.commit()
        return user

    return _create_user
