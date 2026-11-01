"""Responsive multi-viewport test matrix persistence models.

Phase 19 Feature 9: Multi-viewport audit profile execution records,
shared vs unique violation tracking, and responsive matrix summaries.
"""

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import Boolean, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.scan import Scan


class ScanViewportRun(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Execution record for an accessibility audit across a specific viewport profile."""

    __tablename__ = "scan_viewport_runs"

    scan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scans.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    viewport_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,  # 'desktop', 'tablet', 'mobile', or custom name
    )
    width: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    height: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    device_scale_factor: Mapped[float] = mapped_column(
        Float,
        default=1.0,
        nullable=False,
    )
    is_mobile: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        default="completed",
        nullable=False,  # 'completed', 'partial', 'failed'
    )
    total_violations: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    critical_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    serious_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    moderate_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    minor_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    unique_violations_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    findings_summary: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=list,
        nullable=False,
    )

    # Relationships
    scan: Mapped["Scan"] = relationship("Scan")
