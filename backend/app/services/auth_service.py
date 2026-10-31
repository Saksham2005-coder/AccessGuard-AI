"""Authentication and session lifecycle business logic."""

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.errors import AuthenticationError, ConflictError
from app.core.logging import get_logger
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    get_password_hash,
    hash_refresh_token,
    verify_password,
)
from app.db.models.refresh_session import RefreshSession
from app.db.models.user import User
from app.schemas.auth import UserRegisterRequest

logger = get_logger("auth_service")


async def register_user(db: AsyncSession, req: UserRegisterRequest) -> User:
    """Register a new user account with normalized email and Argon2 password hash."""
    normalized_email = req.email.strip().lower()

    # Check for existing account
    existing = await db.execute(select(User).where(User.email == normalized_email))
    if existing.scalar_one_or_none() is not None:
        raise ConflictError("An account with this email address already exists.")

    user = User(
        email=normalized_email,
        password_hash=get_password_hash(req.password),
        display_name=req.display_name.strip() if req.display_name else None,
        is_active=True,
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)

    logger.info("User registered successfully", user_id=str(user.id), email=user.email)
    return user


async def authenticate_user(db: AsyncSession, email: str, password: str) -> User:
    """Authenticate email and password credentials using constant-time verification."""
    normalized_email = email.strip().lower()
    result = await db.execute(select(User).where(User.email == normalized_email))
    user = result.scalar_one_or_none()

    # Uniform error response to avoid user enumeration
    if user is None or not user.is_active or not verify_password(password, user.password_hash):
        logger.info("Authentication failed for user", email=normalized_email)
        raise AuthenticationError("Invalid email or password.")

    return user


async def create_user_session(db: AsyncSession, user: User) -> tuple[str, str]:
    """Create a new access token and refresh session for the authenticated user."""
    settings = get_settings()

    # 1. Create short-lived access token
    access_token = create_access_token(
        subject=user.id,
        expires_delta=timedelta(minutes=settings.JWT_ACCESS_TOKEN_MINUTES),
        extra_claims={"email": user.email},
    )

    # 2. Create long-lived refresh token session in database
    raw_refresh_token, token_hash = generate_refresh_token()
    now = datetime.now(UTC)
    expires_at = now + timedelta(days=settings.JWT_REFRESH_TOKEN_DAYS)

    session = RefreshSession(
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
        is_revoked=False,
    )
    db.add(session)
    await db.flush()

    logger.info("Created user session", user_id=str(user.id), session_id=str(session.id))
    return access_token, raw_refresh_token


async def refresh_user_session(db: AsyncSession, raw_refresh_token: str) -> tuple[str, str, User]:
    """Rotate refresh token and issue a new access token."""
    token_hash = hash_refresh_token(raw_refresh_token)
    now = datetime.now(UTC)

    result = await db.execute(
        select(RefreshSession).where(
            RefreshSession.token_hash == token_hash,
            RefreshSession.is_revoked.is_(False),
            RefreshSession.expires_at > now,
        )
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise AuthenticationError("Invalid or expired refresh token.")

    # Fetch corresponding active user
    user = await get_user_by_id(db, session.user_id)
    if user is None or not user.is_active:
        session.is_revoked = True
        await db.flush()
        raise AuthenticationError("Account is inactive or disabled.")

    # Revoke current refresh session (token rotation)
    session.is_revoked = True

    # Generate new session and token
    new_access_token, new_raw_refresh_token = await create_user_session(db, user)
    return new_access_token, new_raw_refresh_token, user


async def revoke_user_session(db: AsyncSession, raw_refresh_token: str) -> None:
    """Revoke an active refresh session on logout."""
    token_hash = hash_refresh_token(raw_refresh_token)
    result = await db.execute(select(RefreshSession).where(RefreshSession.token_hash == token_hash))
    session = result.scalar_one_or_none()
    if session is not None and not session.is_revoked:
        session.is_revoked = True
        await db.flush()
        logger.info("Revoked user refresh session", session_id=str(session.id))


async def get_user_by_id(db: AsyncSession, user_id: uuid.UUID) -> User | None:
    """Lookup user by primary key UUID."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()
