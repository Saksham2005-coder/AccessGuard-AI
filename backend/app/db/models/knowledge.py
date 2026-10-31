"""Knowledge source and chunk database models for WCAG/ARIA RAG corpus."""

import uuid
from typing import Any

from sqlalchemy import TIMESTAMP, Boolean, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base, utc_now


class KnowledgeSource(Base):
    """Authoritative accessibility knowledge base registry."""

    __tablename__ = "knowledge_sources"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    source_key: Mapped[str] = mapped_column(
        String(160),
        unique=True,
        index=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    source_url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    publisher: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )
    standard_version: Mapped[str | None] = mapped_column(
        String(40),
        nullable=True,
    )
    content_version: Mapped[str | None] = mapped_column(
        String(120),
        nullable=True,
    )
    fetched_at: Mapped[Any | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )
    checksum: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Relationships
    chunks: Mapped[list["KnowledgeChunk"]] = relationship(
        "KnowledgeChunk",
        back_populates="source",
        cascade="all, delete-orphan",
    )


class KnowledgeChunk(Base):
    """Indexed WCAG criterion, understanding section, technique, or ARIA pattern."""

    __tablename__ = "knowledge_chunks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    source_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_sources.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    chunk_key: Mapped[str] = mapped_column(
        String(200),
        unique=True,
        index=True,
        nullable=False,
    )
    criterion_id: Mapped[str | None] = mapped_column(
        String(30),
        index=True,
        nullable=True,
    )
    criterion_level: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
    )
    principle: Mapped[str | None] = mapped_column(
        String(40),
        nullable=True,
    )
    section_title: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    content_type: Mapped[str] = mapped_column(
        String(40),
        index=True,
        nullable=False,
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    source_url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    chunk_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSON().with_variant(JSONB, "postgresql"),
        default=dict,
        nullable=False,
    )
    content_hash: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )
    embedding_model: Mapped[str] = mapped_column(
        String(160),
        nullable=False,
    )
    indexed_at: Mapped[Any | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )
    created_at: Mapped[Any] = mapped_column(
        TIMESTAMP(timezone=True),
        default=utc_now,
        nullable=False,
    )

    # Relationships
    source: Mapped["KnowledgeSource"] = relationship(
        "KnowledgeSource",
        back_populates="chunks",
    )

    __table_args__ = (Index("ix_knowledge_chunks_content_hash", "content_hash"),)
