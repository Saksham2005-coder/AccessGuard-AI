"""Pydantic schemas for project management and domain verification."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.domain_utils import normalize_domain
from app.services.verification_service import (
    get_expected_txt_value,
    get_verification_record_name,
)

if TYPE_CHECKING:
    from app.db.models.domain_verification import ProjectDomainVerification


class ProjectCreateRequest(BaseModel):
    """Payload for creating a new project."""

    name: str = Field(..., min_length=1, max_length=160, description="Project display name")
    base_domain: str = Field(
        ...,
        min_length=3,
        max_length=253,
        description="Domain name to audit (e.g. 'example.com')",
    )

    @field_validator("base_domain", mode="before")
    @classmethod
    def validate_and_normalize_domain(cls, v: object) -> str:
        """Validate and normalize domain using RFC 1035 / RFC 1123 rules."""
        if isinstance(v, str):
            try:
                return normalize_domain(v)
            except Exception as e:
                # Map domain validation errors into standard Pydantic schema validation error
                raise ValueError(str(e)) from e
        raise ValueError("Domain must be a string.")

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str) -> str:
        """Strip surrounding whitespace from project name."""
        stripped = v.strip()
        if not stripped:
            raise ValueError("Project name cannot be empty or whitespace only.")
        return stripped


class ProjectUpdateRequest(BaseModel):
    """Payload for updating an existing project."""

    name: str | None = Field(default=None, min_length=1, max_length=160)

    @field_validator("name")
    @classmethod
    def strip_name(cls, v: str | None) -> str | None:
        """Strip name if provided."""
        if v is not None:
            stripped = v.strip()
            if not stripped:
                raise ValueError("Project name cannot be empty or whitespace only.")
            return stripped
        return v


class DomainVerificationResponse(BaseModel):
    """DNS TXT record verification details and instructions."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    domain: str
    record_name: str
    record_type: str = "TXT"
    expected_value: str
    status: str
    expires_at: datetime
    verified_at: datetime | None = None
    created_at: datetime

    @classmethod
    def from_model(cls, model: "ProjectDomainVerification") -> "DomainVerificationResponse":
        """Build response with computed DNS record name and expected value."""
        return cls(
            id=model.id,
            project_id=model.project_id,
            domain=model.domain,
            record_name=get_verification_record_name(model.domain),
            record_type="TXT",
            expected_value=get_expected_txt_value(model.verification_token),
            status=model.status,
            expires_at=model.expires_at,
            verified_at=model.verified_at,
            created_at=model.created_at,
        )


class ProjectResponse(BaseModel):
    """Project entity response model."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    base_domain: str
    is_verified: bool
    latest_verification: DomainVerificationResponse | None = None
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None = None


class ProjectListResponse(BaseModel):
    """Paginated or listed collection of projects."""

    items: list[ProjectResponse]
    total: int


class VerificationCheckResponse(BaseModel):
    """Outcome of on-demand DNS TXT verification check."""

    verified: bool
    message: str
    status: str
    verification: DomainVerificationResponse
