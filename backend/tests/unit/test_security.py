"""Unit tests for Argon2 password hashing and JWT security functions."""

import uuid
from datetime import timedelta

import pytest

from app.core.errors import AuthenticationError
from app.core.security import (
    create_access_token,
    decode_access_token,
    generate_refresh_token,
    get_password_hash,
    hash_refresh_token,
    verify_password,
)


def test_argon2_password_hashing() -> None:
    """Verify password hashing produces safe hashes and verifies properly."""
    password = "CorrectHorseBatteryStaple123!"
    hashed = get_password_hash(password)

    # Must be hashed, not plaintext
    assert hashed != password
    assert "$argon2" in hashed

    # Valid password verifies
    assert verify_password(password, hashed) is True

    # Wrong password fails
    assert verify_password("WrongPassword!", hashed) is False
    assert verify_password("", hashed) is False


def test_jwt_access_token_creation_and_decoding() -> None:
    """Verify JWT access tokens encode subject and decode cleanly."""
    user_id = uuid.uuid4()
    token = create_access_token(subject=user_id, extra_claims={"email": "alice@example.com"})

    payload = decode_access_token(token)
    assert payload["sub"] == str(user_id)
    assert payload["email"] == "alice@example.com"
    assert payload["type"] == "access"


def test_jwt_access_token_expiry() -> None:
    """Verify expired JWT access tokens are rejected."""
    user_id = uuid.uuid4()
    # Create token expired 1 second in the past
    token = create_access_token(subject=user_id, expires_delta=timedelta(seconds=-1))

    with pytest.raises(AuthenticationError, match="Access token has expired"):
        decode_access_token(token)


def test_refresh_token_generation_and_hashing() -> None:
    """Verify refresh token generation produces cryptographically random tokens and deterministic hashes."""
    raw_1, hash_1 = generate_refresh_token()
    raw_2, hash_2 = generate_refresh_token()

    # Must produce distinct entropy
    assert raw_1 != raw_2
    assert hash_1 != hash_2

    # Hash must be reproducible from raw token
    assert hash_refresh_token(raw_1) == hash_1
    assert hash_refresh_token(raw_2) == hash_2
