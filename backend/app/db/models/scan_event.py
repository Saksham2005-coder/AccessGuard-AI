"""Scan progress and audit event persistence model for real-time observability."""

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import TIMESTAMP, BigInteger, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base, utc_now

if TYPE_CHECKING:
    from app.db.models.scan import Scan


class ScanEvent(Base):
    """Immutable sequence of progress events emitted during scan lifecycle."""

    __tablename__ = "scan_events"
    __table_args__ = (
        UniqueConstraint("scan_id", "sequence_number", name="uq_scan_events_scan_seq"),
    )

    id: Mapped[int] = mapped_column(
        Integer().with_variant(BigInteger, "postgresql"),
        primary_key=True,
        autoincrement=True,
    )
    scan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scans.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    sequence_number: Mapped[int] = mapped_column(
        BigInteger,
        index=True,
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )
    payload: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=dict,
        nullable=False,
    )
    created_at: Mapped[Any] = mapped_column(
        TIMESTAMP(timezone=True),
        default=utc_now,
        nullable=False,
    )

    # Relationships
    scan: Mapped["Scan"] = relationship("Scan")
