"""Pydantic schemas for Accessibility Compliance Passport.

Phase 19 Feature 10: Versioned, tamper-evident audit evidence package with deterministic
SHA-256 integrity hash, multi-engine telemetry breakdown, and audit traceability.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class CompliancePassportSummary(BaseModel):
    """Compact summary of a compliance passport version for listing."""

    id: uuid.UUID
    project_id: uuid.UUID
    version: str
    status: str
    integrity_hash: str
    status_label: str
    total_scans_included: int = 0
    total_violations: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class CompliancePassportDetail(BaseModel):
    """Full detail of a compliance passport version with complete evidence payload."""

    id: uuid.UUID
    project_id: uuid.UUID
    version: str
    status: str
    integrity_hash: str
    evidence_payload: dict[str, Any]
    created_by: uuid.UUID | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class GeneratePassportRequest(BaseModel):
    """Request payload for generating a new immutable compliance passport."""

    notes: str | None = Field(default=None, max_length=1000)


class PassportExportDocument(BaseModel):
    """Formatted human-readable and auditable report document."""

    passport_id: uuid.UUID
    version: str
    integrity_hash: str
    markdown_content: str
    generated_at: datetime
