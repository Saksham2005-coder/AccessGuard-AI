"""Unit tests for Pydantic Settings parsing and validation rules."""

import pytest
from pydantic import ValidationError

from app.config import Settings


def test_default_settings_no_llm_keys_required() -> None:
    """Verify settings initialize successfully in mock mode without Gemini/Groq keys."""
    settings = Settings(
        APP_ENV="development",
        LLM_PROVIDER="mock",
        JWT_SECRET_KEY="dev-secret-key-that-is-valid-length",
    )
    assert settings.LLM_PROVIDER == "mock"
    assert settings.GEMINI_API_KEY is None
    assert settings.GROQ_API_KEY is None


def test_frontend_origins_parsing() -> None:
    """Verify comma-separated frontend origins are parsed correctly."""
    settings = Settings(
        FRONTEND_ORIGINS="https://app.example.com, https://admin.example.com",
        JWT_SECRET_KEY="valid-secret-key-length-check",
    )
    assert settings.FRONTEND_ORIGINS == [
        "https://app.example.com",
        "https://admin.example.com",
    ]


def test_jwt_secret_min_length_validation() -> None:
    """Verify short JWT secret keys are rejected."""
    with pytest.raises(ValidationError) as exc_info:
        Settings(JWT_SECRET_KEY="too-short")
    assert "JWT_SECRET_KEY must be at least 16 characters" in str(exc_info.value)


def test_scanner_limits_bounds_enforced() -> None:
    """Verify server hard limits cannot be exceeded via settings."""
    with pytest.raises(ValidationError):
        Settings(MAX_SCAN_PAGES=200)

    with pytest.raises(ValidationError):
        Settings(MAX_CRAWL_DEPTH=10)


def test_production_security_validation() -> None:
    """Verify production security constraints enforce safe defaults."""
    settings = Settings(
        APP_ENV="production",
        DATABASE_URL="postgresql+psycopg://accessguard:change-me@postgres:5432/accessguard",
        JWT_SECRET_KEY="valid-length-but-production-check",
        COOKIE_SECURE=True,
    )
    with pytest.raises(ValueError, match="Default DATABASE_URL"):
        settings.validate_runtime_security()

    valid_prod = Settings(
        APP_ENV="production",
        DATABASE_URL="postgresql+psycopg://user:prod_password@db.internal:5432/accessguard",
        JWT_SECRET_KEY="a-secure-production-random-secret-key-here",
        COOKIE_SECURE=True,
        TEST_ALLOW_LOOPBACK=False,
    )
    # Should not raise
    valid_prod.validate_runtime_security()
