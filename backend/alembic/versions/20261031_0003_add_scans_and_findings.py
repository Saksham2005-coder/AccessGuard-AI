"""Add scans, scan_pages, findings and finding_nodes tables.

Revision ID: 0003_add_scans_and_findings
Revises: 0002_add_projects
Create Date: 2026-10-31 17:02:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0003_add_scans_and_findings"
down_revision: Union[str, None] = "0002_add_projects"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Scans table
    op.create_table(
        "scans",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("requested_by", sa.UUID(), nullable=False),
        sa.Column("target_url", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="pending"),
        sa.Column(
            "config",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("started_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("completed_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("total_pages", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pages_succeeded", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("pages_failed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_violations", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("axe_version", sa.String(length=40), nullable=True),
        sa.Column("browser_version", sa.String(length=80), nullable=True),
        sa.Column("error_code", sa.String(length=80), nullable=True),
        sa.Column("error_summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
            name=op.f("fk_scans_project_id_projects"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["requested_by"],
            ["users.id"],
            name=op.f("fk_scans_requested_by_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_scans")),
    )
    op.create_index(op.f("ix_scans_project_id"), "scans", ["project_id"], unique=False)
    op.create_index(op.f("ix_scans_requested_by"), "scans", ["requested_by"], unique=False)
    op.create_index(op.f("ix_scans_status"), "scans", ["status"], unique=False)

    # 2. Scan pages table
    op.create_table(
        "scan_pages",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("scan_id", sa.UUID(), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("normalized_url", sa.Text(), nullable=False),
        sa.Column("page_title", sa.Text(), nullable=True),
        sa.Column("http_status", sa.Integer(), nullable=True),
        sa.Column("audit_status", sa.String(length=30), nullable=False, server_default="pending"),
        sa.Column("load_duration_ms", sa.Integer(), nullable=True),
        sa.Column("screenshot_storage_key", sa.Text(), nullable=True),
        sa.Column("dom_snapshot_storage_key", sa.Text(), nullable=True),
        sa.Column("error_code", sa.String(length=80), nullable=True),
        sa.Column("error_summary", sa.Text(), nullable=True),
        sa.Column("scanned_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["scan_id"],
            ["scans.id"],
            name=op.f("fk_scan_pages_scan_id_scans"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_scan_pages")),
        sa.UniqueConstraint("scan_id", "normalized_url", name="uq_scan_pages_scan_normalized_url"),
    )
    op.create_index(op.f("ix_scan_pages_scan_id"), "scan_pages", ["scan_id"], unique=False)
    op.create_index(op.f("ix_scan_pages_normalized_url"), "scan_pages", ["normalized_url"], unique=False)

    # 3. Findings table
    op.create_table(
        "findings",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("scan_page_id", sa.UUID(), nullable=False),
        sa.Column("axe_rule_id", sa.String(length=160), nullable=False),
        sa.Column("impact", sa.String(length=20), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("help", sa.Text(), nullable=True),
        sa.Column("help_url", sa.Text(), nullable=True),
        sa.Column(
            "wcag_tags",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("selector", sa.Text(), nullable=True),
        sa.Column("html_snippet", sa.Text(), nullable=True),
        sa.Column("failure_summary", sa.Text(), nullable=True),
        sa.Column("fingerprint", sa.String(length=128), nullable=False),
        sa.Column("is_incomplete", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["scan_page_id"],
            ["scan_pages.id"],
            name=op.f("fk_findings_scan_page_id_scan_pages"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_findings")),
    )
    op.create_index(op.f("ix_findings_scan_page_id"), "findings", ["scan_page_id"], unique=False)
    op.create_index(op.f("ix_findings_axe_rule_id"), "findings", ["axe_rule_id"], unique=False)
    op.create_index(op.f("ix_findings_fingerprint"), "findings", ["fingerprint"], unique=False)

    # 4. Finding nodes table
    op.create_table(
        "finding_nodes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("finding_id", sa.UUID(), nullable=False),
        sa.Column(
            "target",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
            server_default="[]",
        ),
        sa.Column("html_snippet", sa.Text(), nullable=True),
        sa.Column("failure_summary", sa.Text(), nullable=True),
        sa.Column("screenshot_reference", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["finding_id"],
            ["findings.id"],
            name=op.f("fk_finding_nodes_finding_id_findings"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_finding_nodes")),
    )
    op.create_index(op.f("ix_finding_nodes_finding_id"), "finding_nodes", ["finding_id"], unique=False)


def downgrade() -> None:
    op.drop_table("finding_nodes")
    op.drop_table("findings")
    op.drop_table("scan_pages")
    op.drop_table("scans")
