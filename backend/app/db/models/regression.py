"""Regression monitoring, scheduled scans, and in-app notifications persistence models.

Phase 19 Feature 6: Historical accessibility regression tracking, pinned baselines,
scheduled recurring audits, and notification dispatch.
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import TIMESTAMP, Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.project import Project
    from app.db.models.scan import Scan
    from app.db.models.user import User


class ProjectBaseline(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """User-pinned or designated historical audit baseline for an accessibility project."""

    __tablename__ = "project_baselines"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    scan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scans.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    pinned_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project")
    scan: Mapped["Scan"] = relationship("Scan")
    user: Mapped["User"] = relationship("User")


class ScanSchedule(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Recurring scheduled accessibility scan configuration for an authorized project."""

    __tablename__ = "scan_schedules"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    cadence: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default="weekly",
    )  # daily, weekly, biweekly, monthly
    target_url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    last_run_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )
    next_run_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )
    last_scan_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    notify_on_regression: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project")
    owner: Mapped["User"] = relationship("User")


class InAppNotification(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """In-app accessibility notification alerting users to regressions or audit results."""

    __tablename__ = "in_app_notifications"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
        nullable=True,
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )
    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    notification_type: Mapped[str] = mapped_column(
        String(60),
        nullable=False,
        default="regression_detected",
    )  # regression_detected, schedule_alert, scan_completed
    link_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    is_read: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User")
    project: Mapped["Project | None"] = relationship("Project")
