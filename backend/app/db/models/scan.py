"""Scan job execution persistence model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import TIMESTAMP, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.project import Project
    from app.db.models.scan_page import ScanPage
    from app.db.models.user import User


class Scan(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Scan job entity orchestrating multi-page accessibility auditing."""

    __tablename__ = "scans"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    requested_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    target_url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(40),
        default="pending",
        index=True,
        nullable=False,
    )  # pending, running, completed, failed, cancelled
    config: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=dict,
        nullable=False,
    )
    started_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )
    total_pages: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    pages_succeeded: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    pages_failed: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    total_violations: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    axe_version: Mapped[str | None] = mapped_column(
        String(40),
        nullable=True,
    )
    browser_version: Mapped[str | None] = mapped_column(
        String(80),
        nullable=True,
    )
    error_code: Mapped[str | None] = mapped_column(
        String(80),
        nullable=True,
    )
    error_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project")
    requester: Mapped["User"] = relationship("User")
    pages: Mapped[list["ScanPage"]] = relationship(
        "ScanPage",
        back_populates="scan",
        cascade="all, delete-orphan",
        order_by="desc(ScanPage.created_at)",
    )
