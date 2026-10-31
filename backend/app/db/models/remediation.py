"""Remediation proposals, human approvals, and snapshot validation persistence models."""

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.finding import Finding
    from app.db.models.user import User


class Remediation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """AI-proposed remediation and code patch for an accessibility finding."""

    __tablename__ = "remediations"

    finding_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("findings.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        default="proposed",
        index=True,
        nullable=False,
    )  # proposed, needs_review, approved, rejected, validating, validated, validation_failed, manual_review_required
    root_cause: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    recommendation: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    patch_format: Mapped[str] = mapped_column(
        String(40),
        default="snippet",
        nullable=False,
    )  # snippet, dom_operations, manual_steps
    patch_payload: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=dict,
        nullable=False,
    )
    before_snippet: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    after_snippet: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    confidence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )
    model_provider: Mapped[str | None] = mapped_column(
        String(40),
        nullable=True,
    )
    model_name: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
    )
    prompt_version: Mapped[str | None] = mapped_column(
        String(40),
        nullable=True,
    )

    # Relationships
    finding: Mapped["Finding"] = relationship("Finding")
    approvals: Mapped[list["RemediationApproval"]] = relationship(
        "RemediationApproval",
        back_populates="remediation",
        cascade="all, delete-orphan",
        order_by="RemediationApproval.created_at.desc()",
    )
    validation_results: Mapped[list["ValidationResult"]] = relationship(
        "ValidationResult",
        back_populates="remediation",
        cascade="all, delete-orphan",
        order_by="ValidationResult.created_at.desc()",
    )


class RemediationApproval(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Human audit record approving or rejecting a proposed accessibility remediation."""

    __tablename__ = "remediation_approvals"

    remediation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("remediations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    reviewer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    decision: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )  # approved, rejected
    comments: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    remediation: Mapped["Remediation"] = relationship("Remediation", back_populates="approvals")
    reviewer: Mapped["User"] = relationship("User")


class ValidationResult(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Isolated DOM snapshot or fixture test verification outcome for a remediation patch."""

    __tablename__ = "validation_results"

    remediation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("remediations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    validation_mode: Mapped[str] = mapped_column(
        String(40),
        default="dom_snapshot",
        nullable=False,
    )  # dom_snapshot, local_fixture, repository_test
    passed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    original_rule_resolved: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    new_violations: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=list,
        nullable=False,
    )
    details: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=dict,
        nullable=False,
    )

    # Relationships
    remediation: Mapped["Remediation"] = relationship(
        "Remediation", back_populates="validation_results"
    )
