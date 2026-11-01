"""Add scan_viewport_runs table.

Revision ID: 0011_add_scan_viewport_runs
Revises: 0010_add_assistant_conversations
Create Date: 2026-11-01 18:10:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0011_add_scan_viewport_runs"
down_revision: str | None = "0010_add_assistant_conversations"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "scan_viewport_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "scan_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("scans.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("viewport_name", sa.String(50), nullable=False),
        sa.Column("width", sa.Integer(), nullable=False),
        sa.Column("height", sa.Integer(), nullable=False),
        sa.Column("device_scale_factor", sa.Float(), server_default="1.0", nullable=False),
        sa.Column("is_mobile", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.Column("status", sa.String(30), server_default="completed", nullable=False),
        sa.Column("total_violations", sa.Integer(), server_default="0", nullable=False),
        sa.Column("critical_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("serious_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("moderate_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("minor_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("unique_violations_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "findings_summary",
            sa.JSON().with_variant(postgresql.JSONB, "postgresql"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table("scan_viewport_runs")
