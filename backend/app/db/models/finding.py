"""Accessibility finding and finding node persistence models."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.scan_page import ScanPage


class Finding(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Accessibility violation or manual-review item detected on an audited page."""

    __tablename__ = "findings"

    scan_page_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scan_pages.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    axe_rule_id: Mapped[str] = mapped_column(
        String(160),
        index=True,
        nullable=False,
    )
    impact: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )  # minor, moderate, serious, critical
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    help: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    help_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    wcag_tags: Mapped[list[str]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=list,
        nullable=False,
    )
    selector: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    html_snippet: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    failure_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    fingerprint: Mapped[str] = mapped_column(
        String(128),
        index=True,
        nullable=False,
    )
    is_incomplete: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Relationships
    scan_page: Mapped["ScanPage"] = relationship("ScanPage", back_populates="findings")
    nodes: Mapped[list["FindingNode"]] = relationship(
        "FindingNode",
        back_populates="finding",
        cascade="all, delete-orphan",
    )


class FindingNode(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Specific DOM element node associated with an accessibility finding."""

    __tablename__ = "finding_nodes"

    finding_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("findings.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    target: Mapped[list[str]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=list,
        nullable=False,
    )
    html_snippet: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    failure_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    screenshot_reference: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    finding: Mapped["Finding"] = relationship("Finding", back_populates="nodes")
