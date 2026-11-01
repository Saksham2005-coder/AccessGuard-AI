"""Add heatmap geometry and viewport columns to scan_pages, findings, and finding_nodes.

Revision ID: 0007_add_heatmap_geometry
Revises: 0006_add_remediations_and_agent_runs
Create Date: 2026-11-01 16:00:00.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0007_add_heatmap_geometry"
down_revision: str | None = "0006_add_remediations_and_agent_runs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. scan_pages viewport and device pixel ratio columns
    op.add_column(
        "scan_pages",
        sa.Column("viewport_width", sa.Integer(), nullable=True, server_default="1280"),
    )
    op.add_column(
        "scan_pages",
        sa.Column("viewport_height", sa.Integer(), nullable=True, server_default="800"),
    )
    op.add_column(
        "scan_pages",
        sa.Column("device_pixel_ratio", sa.Float(), nullable=True, server_default="1.0"),
    )

    # 2. findings bounding_box and geometry_status
    op.add_column(
        "findings",
        sa.Column(
            "bounding_box",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=True,
        ),
    )
    op.add_column(
        "findings",
        sa.Column(
            "geometry_status",
            sa.String(length=30),
            nullable=True,
            server_default="not_located",
        ),
    )

    # 3. finding_nodes bounding_box and geometry_status
    op.add_column(
        "finding_nodes",
        sa.Column(
            "bounding_box",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=True,
        ),
    )
    op.add_column(
        "finding_nodes",
        sa.Column(
            "geometry_status",
            sa.String(length=30),
            nullable=True,
            server_default="not_located",
        ),
    )


def downgrade() -> None:
    op.drop_column("finding_nodes", "geometry_status")
    op.drop_column("finding_nodes", "bounding_box")
    op.drop_column("findings", "geometry_status")
    op.drop_column("findings", "bounding_box")
    op.drop_column("scan_pages", "device_pixel_ratio")
    op.drop_column("scan_pages", "viewport_height")
    op.drop_column("scan_pages", "viewport_width")
