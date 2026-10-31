"""Add agent_runs, remediations, remediation_approvals, and validation_results tables.

Revision ID: 0006_add_remediations_and_agent_runs
Revises: 0005_add_knowledge_tables
Create Date: 2026-10-31 19:35:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0006_add_remediations_and_agent_runs"
down_revision: Union[str, None] = "0005_add_knowledge_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. agent_runs table
    op.create_table(
        "agent_runs",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("scan_id", sa.UUID(), nullable=False),
        sa.Column("finding_id", sa.UUID(), nullable=True),
        sa.Column("agent_name", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column(
            "input_summary",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
            server_default="{}",
        ),
        sa.Column(
            "output_summary",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("provider", sa.String(length=40), nullable=True),
        sa.Column("model_name", sa.String(length=120), nullable=True),
        sa.Column("prompt_version", sa.String(length=40), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("error_code", sa.String(length=80), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["finding_id"],
            ["findings.id"],
            name=op.f("fk_agent_runs_finding_id_findings"),
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["scan_id"],
            ["scans.id"],
            name=op.f("fk_agent_runs_scan_id_scans"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_agent_runs")),
    )
    op.create_index(op.f("ix_agent_runs_agent_name"), "agent_runs", ["agent_name"], unique=False)
    op.create_index(op.f("ix_agent_runs_finding_id"), "agent_runs", ["finding_id"], unique=False)
    op.create_index(op.f("ix_agent_runs_scan_id"), "agent_runs", ["scan_id"], unique=False)
    op.create_index(op.f("ix_agent_runs_status"), "agent_runs", ["status"], unique=False)

    # 2. remediations table
    op.create_table(
        "remediations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("finding_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="proposed"),
        sa.Column("root_cause", sa.Text(), nullable=False),
        sa.Column("recommendation", sa.Text(), nullable=False),
        sa.Column("patch_format", sa.String(length=40), nullable=False, server_default="snippet"),
        sa.Column(
            "patch_payload",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("before_snippet", sa.Text(), nullable=True),
        sa.Column("after_snippet", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("model_provider", sa.String(length=40), nullable=True),
        sa.Column("model_name", sa.String(length=120), nullable=True),
        sa.Column("prompt_version", sa.String(length=40), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["finding_id"],
            ["findings.id"],
            name=op.f("fk_remediations_finding_id_findings"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_remediations")),
    )
    op.create_index(op.f("ix_remediations_finding_id"), "remediations", ["finding_id"], unique=False)
    op.create_index(op.f("ix_remediations_status"), "remediations", ["status"], unique=False)

    # 3. remediation_approvals table
    op.create_table(
        "remediation_approvals",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("remediation_id", sa.UUID(), nullable=False),
        sa.Column("reviewer_id", sa.UUID(), nullable=False),
        sa.Column("decision", sa.String(length=20), nullable=False),
        sa.Column("comments", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["remediation_id"],
            ["remediations.id"],
            name=op.f("fk_remediation_approvals_remediation_id_remediations"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["reviewer_id"],
            ["users.id"],
            name=op.f("fk_remediation_approvals_reviewer_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_remediation_approvals")),
    )
    op.create_index(
        op.f("ix_remediation_approvals_remediation_id"),
        "remediation_approvals",
        ["remediation_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_remediation_approvals_reviewer_id"),
        "remediation_approvals",
        ["reviewer_id"],
        unique=False,
    )

    # 4. validation_results table
    op.create_table(
        "validation_results",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("remediation_id", sa.UUID(), nullable=False),
        sa.Column("validation_mode", sa.String(length=40), nullable=False, server_default="dom_snapshot"),
        sa.Column("passed", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("original_rule_resolved", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "new_violations",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
            server_default="[]",
        ),
        sa.Column(
            "details",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["remediation_id"],
            ["remediations.id"],
            name=op.f("fk_validation_results_remediation_id_remediations"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_validation_results")),
    )
    op.create_index(
        op.f("ix_validation_results_remediation_id"),
        "validation_results",
        ["remediation_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_validation_results_remediation_id"), table_name="validation_results")
    op.drop_table("validation_results")
    op.drop_index(op.f("ix_remediation_approvals_reviewer_id"), table_name="remediation_approvals")
    op.drop_index(op.f("ix_remediation_approvals_remediation_id"), table_name="remediation_approvals")
    op.drop_table("remediation_approvals")
    op.drop_index(op.f("ix_remediations_status"), table_name="remediations")
    op.drop_index(op.f("ix_remediations_finding_id"), table_name="remediations")
    op.drop_table("remediations")
    op.drop_index(op.f("ix_agent_runs_status"), table_name="agent_runs")
    op.drop_index(op.f("ix_agent_runs_scan_id"), table_name="agent_runs")
    op.drop_index(op.f("ix_agent_runs_finding_id"), table_name="agent_runs")
    op.drop_index(op.f("ix_agent_runs_agent_name"), table_name="agent_runs")
    op.drop_table("agent_runs")
