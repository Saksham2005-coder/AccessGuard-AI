"""Add knowledge_sources and knowledge_chunks tables for WCAG RAG corpus.

Revision ID: 0005_add_knowledge_tables
Revises: 0004_add_scan_events
Create Date: 2026-10-31 17:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0005_add_knowledge_tables"
down_revision: Union[str, None] = "0004_add_scan_events"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "knowledge_sources",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("source_key", sa.String(length=160), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("publisher", sa.String(length=120), nullable=False),
        sa.Column("standard_version", sa.String(length=40), nullable=True),
        sa.Column("content_version", sa.String(length=120), nullable=True),
        sa.Column("fetched_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("checksum", sa.String(length=128), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_knowledge_sources")),
        sa.UniqueConstraint("source_key", name=op.f("uq_knowledge_sources_source_key")),
    )
    op.create_index(
        op.f("ix_knowledge_sources_source_key"), "knowledge_sources", ["source_key"], unique=True
    )

    op.create_table(
        "knowledge_chunks",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("source_id", sa.UUID(), nullable=False),
        sa.Column("chunk_key", sa.String(length=200), nullable=False),
        sa.Column("criterion_id", sa.String(length=30), nullable=True),
        sa.Column("criterion_level", sa.String(length=10), nullable=True),
        sa.Column("principle", sa.String(length=40), nullable=True),
        sa.Column("section_title", sa.Text(), nullable=True),
        sa.Column("content_type", sa.String(length=40), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column(
            "metadata",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("content_hash", sa.String(length=128), nullable=False),
        sa.Column("embedding_model", sa.String(length=160), nullable=False),
        sa.Column("indexed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["source_id"],
            ["knowledge_sources.id"],
            name=op.f("fk_knowledge_chunks_source_id_knowledge_sources"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_knowledge_chunks")),
        sa.UniqueConstraint("chunk_key", name=op.f("uq_knowledge_chunks_chunk_key")),
    )
    op.create_index(
        op.f("ix_knowledge_chunks_chunk_key"), "knowledge_chunks", ["chunk_key"], unique=True
    )
    op.create_index(
        op.f("ix_knowledge_chunks_criterion_id"), "knowledge_chunks", ["criterion_id"], unique=False
    )
    op.create_index(
        op.f("ix_knowledge_chunks_content_type"), "knowledge_chunks", ["content_type"], unique=False
    )
    op.create_index(
        op.f("ix_knowledge_chunks_source_id"), "knowledge_chunks", ["source_id"], unique=False
    )
    op.create_index(
        op.f("ix_knowledge_chunks_content_hash"), "knowledge_chunks", ["content_hash"], unique=False
    )


def downgrade() -> None:
    op.drop_table("knowledge_chunks")
    op.drop_table("knowledge_sources")
