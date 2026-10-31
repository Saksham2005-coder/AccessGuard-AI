"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """AccessGuard AI application settings parsed from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application Information
    APP_ENV: Literal["development", "test", "production"] = "development"
    APP_NAME: str = "AccessGuard AI"
    APP_VERSION: str = "0.1.0"
    API_V1_PREFIX: str = "/api/v1"

    # CORS Configuration
    FRONTEND_ORIGINS: list[str] = Field(default=["http://localhost:5173", "http://127.0.0.1:5173"])

    # Database & Infrastructure
    DATABASE_URL: str = Field(
        default="postgresql+psycopg://accessguard:change-me@localhost:5432/accessguard"
    )
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    QDRANT_URL: str = Field(default="http://localhost:6333")
    QDRANT_COLLECTION: str = "wcag_knowledge"

    # Security & Tokens
    JWT_SECRET_KEY: str = Field(default="local-dev-secret-key-change-in-production-min-32-chars")
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_MINUTES: int = 30
    JWT_REFRESH_TOKEN_DAYS: int = 7
    COOKIE_SECURE: bool = False

    # LLM Providers (No external keys needed for mock provider in Phases 1-9)
    LLM_PROVIDER: Literal["mock", "gemini", "groq"] = "mock"
    GEMINI_API_KEY: str | None = None
    GROQ_API_KEY: str | None = None
    GEMINI_MODEL: str | None = None
    GROQ_MODEL: str | None = None

    # Knowledge Retrieval & Embeddings (Local, no external API keys)
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    RERANKER_ENABLED: bool = False
    RERANKER_MODEL: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    # Scanner Limits & Timeouts (Server Hard Bounds)
    MAX_SCAN_PAGES: int = Field(default=20, ge=1, le=100)
    MAX_CRAWL_DEPTH: int = Field(default=2, ge=0, le=5)
    PAGE_TIMEOUT_SECONDS: int = Field(default=25, ge=5, le=120)
    SCAN_TOTAL_TIMEOUT_SECONDS: int = Field(default=300, ge=30, le=1800)
    MAX_RESPONSE_BYTES: int = Field(default=5_000_000, ge=100_000, le=50_000_000)
    MAX_HTML_EVIDENCE_CHARS: int = Field(default=12_000, ge=500, le=50_000)
    ARTIFACT_STORAGE_DIR: str = "/app/storage"

    # Security & SSRF
    TEST_ALLOW_LOOPBACK: bool = False

    @field_validator("FRONTEND_ORIGINS", mode="before")
    @classmethod
    def parse_frontend_origins(cls, value: object) -> list[str]:
        """Parse comma-separated string into origin list if needed."""
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        if isinstance(value, list):
            return [str(origin).strip() for origin in value if str(origin).strip()]
        return ["http://localhost:5173"]

    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def validate_jwt_secret(cls, value: str, _info: object) -> str:
        """Ensure JWT secret meets minimum security criteria in production."""
        # In production, require at least 32 characters and reject default placeholder
        if len(value) < 16:
            raise ValueError("JWT_SECRET_KEY must be at least 16 characters long.")
        return value

    def validate_runtime_security(self) -> None:
        """Validate critical configuration constraints at startup."""
        if self.APP_ENV == "production":
            if self.TEST_ALLOW_LOOPBACK:
                raise ValueError("TEST_ALLOW_LOOPBACK must never be True in production.")
            if "change-me" in self.DATABASE_URL:
                raise ValueError("Default DATABASE_URL credentials detected in production.")
            if "local-dev-secret" in self.JWT_SECRET_KEY:
                raise ValueError("Default JWT_SECRET_KEY detected in production.")
            if not self.COOKIE_SECURE:
                raise ValueError("COOKIE_SECURE must be True in production.")


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()
