"""Scan page persistence model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import TIMESTAMP, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.finding import Finding
    from app.db.models.scan import Scan


class ScanPage(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Represents a specific web page crawled and audited within a scan job."""

    __tablename__ = "scan_pages"
    __table_args__ = (
        UniqueConstraint("scan_id", "normalized_url", name="uq_scan_pages_scan_normalized_url"),
    )

    scan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scans.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    normalized_url: Mapped[str] = mapped_column(
        Text,
        index=True,
        nullable=False,
    )
    page_title: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    http_status: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    audit_status: Mapped[str] = mapped_column(
        String(30),
        default="pending",
        nullable=False,
    )  # pending, completed, failed, skipped
    load_duration_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    screenshot_storage_key: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    dom_snapshot_storage_key: Mapped[str | None] = mapped_column(
        Text,
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
    scanned_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )

    # Relationships
    scan: Mapped["Scan"] = relationship("Scan", back_populates="pages")
    findings: Mapped[list["Finding"]] = relationship(
        "Finding",
        back_populates="scan_page",
        cascade="all, delete-orphan",
        order_by="desc(Finding.created_at)",
    )
