"""FastAPI dependency injection wiring."""

from typing import Annotated, Any

from fastapi import Depends

from app.config import Settings, get_settings


def get_current_settings() -> Settings:
    """Dependency returning current application settings."""
    return get_settings()


SettingsDep = Annotated[Settings, Depends(get_current_settings)]


async def get_db_session() -> Any:
    """Dependency yielding async database session placeholder."""
    # Wired to SQLAlchemy AsyncSession in Phase 3
    yield None


async def get_current_active_user() -> Any:
    """Dependency returning authenticated user placeholder."""
    # Wired to JWT session validation in Phase 3
    return None
