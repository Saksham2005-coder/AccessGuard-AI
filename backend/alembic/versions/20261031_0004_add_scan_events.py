"""Add scan_events table for progress events and SSE replay.

Revision ID: 0004_add_scan_events
Revises: 0003_add_scans_and_findings
Create Date: 2026-10-31 17:07:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0004_add_scan_events"
down_revision: str | None = "0003_add_scans_and_findings"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "scan_events",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("scan_id", sa.UUID(), nullable=False),
        sa.Column("sequence_number", sa.BigInteger(), nullable=False),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column(
            "payload",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["scan_id"],
            ["scans.id"],
            name=op.f("fk_scan_events_scan_id_scans"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_scan_events")),
        sa.UniqueConstraint("scan_id", "sequence_number", name="uq_scan_events_scan_seq"),
    )
    op.create_index(op.f("ix_scan_events_scan_id"), "scan_events", ["scan_id"], unique=False)
    op.create_index(
        op.f("ix_scan_events_sequence_number"), "scan_events", ["sequence_number"], unique=False
    )


def downgrade() -> None:
    op.drop_table("scan_events")
