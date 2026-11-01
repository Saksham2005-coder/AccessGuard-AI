"""Database model for Accessibility Compliance Passport.

Phase 19 Feature 10: Versioned, tamper-evident audit evidence package
with deterministic SHA-256 integrity hash and audit traceability.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.project import Project


class CompliancePassport(Base):
    """Immutable, versioned accessibility evidence package with SHA-256 integrity hash."""

    __tablename__ = "compliance_passports"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="v1",
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="completed",
    )
    integrity_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )
    # Use JSONB on Postgres, JSON fallback on SQLite
    evidence_payload: Mapped[dict[str, Any]] = mapped_column(
        JSONB().with_variant(JSON(), "sqlite"),
        nullable=False,
        default=dict,
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    project: Mapped[Project] = relationship(
        "Project",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_compliance_passports_project_version", "project_id", "version", unique=True),
        Index("ix_compliance_passports_hash", "integrity_hash"),
    )
