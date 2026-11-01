"""Add compliance_passports table.

Revision ID: 0012_add_compliance_passports
Revises: 0011_add_scan_viewport_runs
Create Date: 2026-11-01 18:25:00.000000
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0012_add_compliance_passports"
down_revision: str | None = "0011_add_scan_viewport_runs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "compliance_passports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("version", sa.String(length=32), nullable=False, server_default="v1"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="completed"),
        sa.Column("integrity_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "evidence_payload",
            postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite"),
            nullable=False,
        ),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_compliance_passports_project_version",
        "compliance_passports",
        ["project_id", "version"],
        unique=True,
    )
    op.create_index(
        "ix_compliance_passports_hash",
        "compliance_passports",
        ["integrity_hash"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_compliance_passports_hash", table_name="compliance_passports")
    op.drop_index("ix_compliance_passports_project_version", table_name="compliance_passports")
    op.drop_table("compliance_passports")
