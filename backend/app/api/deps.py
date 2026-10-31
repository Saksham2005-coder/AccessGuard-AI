"""FastAPI dependency injection wiring for settings, database sessions, and auth."""

import uuid
from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, get_settings
from app.core.errors import AuthenticationError
from app.core.security import decode_access_token
from app.db.models.user import User
from app.db.session import get_db as db_session_generator
from app.services.auth_service import get_user_by_id

http_bearer = HTTPBearer(auto_error=False)


def get_current_settings() -> Settings:
    """Dependency returning current application settings."""
    return get_settings()


SettingsDep = Annotated[Settings, Depends(get_current_settings)]


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency yielding an active async SQLAlchemy database session."""
    async for session in db_session_generator():
        yield session


DbDep = Annotated[AsyncSession, Depends(get_db_session)]


async def get_current_user(
    db: DbDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(http_bearer)],
) -> User:
    """Dependency verifying access token and returning authenticated user."""
    if credentials is None or not credentials.credentials:
        raise AuthenticationError("Authentication token is missing.")

    payload = decode_access_token(credentials.credentials)
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise AuthenticationError("Invalid token subject.")

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError as e:
        raise AuthenticationError("Invalid user ID format in token.") from e

    user = await get_user_by_id(db, user_id)
    if user is None or not user.is_active:
        raise AuthenticationError("User account not found or disabled.")

    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]
