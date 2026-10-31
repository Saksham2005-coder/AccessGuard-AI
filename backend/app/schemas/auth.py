"""Pydantic schemas for user registration, authentication, and session tokens."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserRegisterRequest(BaseModel):
    """Payload for user account registration."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, max_length=128, description="Account password")
    display_name: str | None = Field(default=None, max_length=120, description="Display name")

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: object) -> str:
        """Normalize email by stripping whitespace and converting to lowercase."""
        if isinstance(v, str):
            return v.strip().lower()
        return str(v).lower()


class UserLoginRequest(BaseModel):
    """Payload for user login."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="Account password")

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: object) -> str:
        """Normalize email by stripping whitespace and converting to lowercase."""
        if isinstance(v, str):
            return v.strip().lower()
        return str(v).lower()


class UserResponse(BaseModel):
    """Safe user profile response omitting password hashes."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    display_name: str | None = None
    is_active: bool
    created_at: datetime


class TokenResponse(BaseModel):
    """Authentication token response payload."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    """Optional payload for explicit refresh token submission."""

    refresh_token: str | None = None


class UserUpdateRequest(BaseModel):
    """Payload for updating user profile."""

    display_name: str | None = Field(default=None, max_length=120, description="Display name")


class ChangePasswordRequest(BaseModel):
    """Payload for changing account password."""

    current_password: str = Field(..., description="Current account password")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")
    confirm_password: str = Field(..., description="Confirmation of new password")

    @field_validator("confirm_password")
    @classmethod
    def passwords_match(cls, v: str, info: object) -> str:
        """Ensure new password and confirmation match."""
        if hasattr(info, "data") and "new_password" in info.data and v != info.data["new_password"]:
            raise ValueError("New password and confirmation password do not match.")
        return v


class MessageResponse(BaseModel):
    """Generic confirmation response."""

    message: str
