"""Conversational Accessibility Assistant database models.

Phase 19 Feature 8: Scoped conversation sessions and grounded dialogue messages with
evidence links, citations, and structured reasoning.
"""

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.project import Project
    from app.db.models.scan import Scan
    from app.db.models.user import User


class AssistantConversation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Contextual conversation session scoped to a user and project/scan."""

    __tablename__ = "assistant_conversations"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    scan_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scans.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project")
    scan: Mapped["Scan | None"] = relationship("Scan")
    user: Mapped["User"] = relationship("User")
    messages: Mapped[list["AssistantMessage"]] = relationship(
        "AssistantMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="AssistantMessage.created_at",
    )


class AssistantMessage(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Individual dialogue turn in an assistant conversation."""

    __tablename__ = "assistant_messages"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assistant_conversations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,  # 'user' | 'assistant'
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    structured_data: Mapped[dict[str, Any] | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=True,
    )

    # Relationships
    conversation: Mapped["AssistantConversation"] = relationship(
        "AssistantConversation", back_populates="messages"
    )
