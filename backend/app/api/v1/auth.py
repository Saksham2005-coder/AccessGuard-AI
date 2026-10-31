"""Authentication endpoints for registration, login, refresh, logout, and current user."""

from typing import Annotated

from fastapi import APIRouter, Cookie, Response, status

from app.api.deps import CurrentUserDep, DbDep, SettingsDep
from app.core.errors import AuthenticationError
from app.db.models.user import User
from app.schemas.auth import (
    MessageResponse,
    RefreshTokenRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


def set_refresh_cookie(response: Response, refresh_token: str, settings: SettingsDep) -> None:
    """Set secure, HttpOnly refresh token cookie on response."""
    max_age_seconds = settings.JWT_REFRESH_TOKEN_DAYS * 24 * 60 * 60
    response.set_cookie(
        key="accessguard_refresh_token",
        value=refresh_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        max_age=max_age_seconds,
        path="/api/v1/auth",
    )


def clear_refresh_cookie(response: Response) -> None:
    """Clear refresh token cookie."""
    response.delete_cookie(
        key="accessguard_refresh_token",
        httponly=True,
        samesite="lax",
        path="/api/v1/auth",
    )


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register Account",
)
async def register(
    req: UserRegisterRequest,
    db: DbDep,
) -> User:
    """Register a new user account with unique email address."""
    return await auth_service.register_user(db, req)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate User",
)
async def login(
    req: UserLoginRequest,
    db: DbDep,
    settings: SettingsDep,
    response: Response,
) -> TokenResponse:
    """Authenticate credentials, establish session, and return JWT access token."""
    user = await auth_service.authenticate_user(db, req.email, req.password)
    access_token, raw_refresh_token = await auth_service.create_user_session(db, user)

    # Attach secure cookie
    set_refresh_cookie(response, raw_refresh_token, settings)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_MINUTES * 60,
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh Session Token",
)
async def refresh(
    db: DbDep,
    settings: SettingsDep,
    response: Response,
    body: RefreshTokenRequest | None = None,
    cookie_token: Annotated[str | None, Cookie(alias="accessguard_refresh_token")] = None,
) -> TokenResponse:
    """Rotate refresh token and issue a fresh access token."""
    token_to_use = (body.refresh_token if body and body.refresh_token else None) or cookie_token
    if not token_to_use:
        raise AuthenticationError("Refresh token missing from request body and cookie.")

    new_access_token, new_raw_refresh_token, user = await auth_service.refresh_user_session(
        db, token_to_use
    )

    set_refresh_cookie(response, new_raw_refresh_token, settings)

    return TokenResponse(
        access_token=new_access_token,
        token_type="bearer",
        expires_in=settings.JWT_ACCESS_TOKEN_MINUTES * 60,
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Revoke Session",
)
async def logout(
    db: DbDep,
    response: Response,
    body: RefreshTokenRequest | None = None,
    cookie_token: Annotated[str | None, Cookie(alias="accessguard_refresh_token")] = None,
) -> MessageResponse:
    """Revoke active refresh token session and clear authentication cookie."""
    token_to_revoke = (body.refresh_token if body and body.refresh_token else None) or cookie_token
    if token_to_revoke:
        await auth_service.revoke_user_session(db, token_to_revoke)

    clear_refresh_cookie(response)
    return MessageResponse(message="Successfully logged out.")


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get Current User Profile",
)
async def get_me(
    current_user: CurrentUserDep,
) -> User:
    """Return profile data for the authenticated session user."""
    return current_user
