"""Agent execution audit log model."""

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.finding import Finding
    from app.db.models.scan import Scan


class AgentRun(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Audit record capturing multi-agent execution metadata, latency, and model metrics."""

    __tablename__ = "agent_runs"

    scan_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scans.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    finding_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("findings.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    agent_name: Mapped[str] = mapped_column(
        String(80),
        index=True,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        index=True,
        nullable=False,
    )  # started, completed, failed, manual_review_required
    input_summary: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=dict,
        nullable=False,
    )
    output_summary: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=dict,
        nullable=False,
    )
    provider: Mapped[str | None] = mapped_column(
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
    duration_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    error_code: Mapped[str | None] = mapped_column(
        String(80),
        nullable=True,
    )

    # Relationships
    scan: Mapped["Scan"] = relationship("Scan")
    finding: Mapped["Finding | None"] = relationship("Finding")
