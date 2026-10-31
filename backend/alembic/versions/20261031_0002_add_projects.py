"""Add projects and domain verification tables.

Revision ID: 0002_add_projects
Revises: 0001_initial_auth
Create Date: 2026-10-31 16:42:00 UTC

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0002_add_projects"
down_revision: str | None = "0001_initial_auth"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "projects",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "owner_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE", name="fk_projects_owner_id_users"),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("base_domain", sa.String(length=253), nullable=False),
        sa.Column("archived_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False),
    )
    op.create_index("ix_projects_owner_id", "projects", ["owner_id"], unique=False)
    op.create_index("ix_projects_base_domain", "projects", ["base_domain"], unique=False)

    op.create_table(
        "project_domain_verifications",
        sa.Column("id", sa.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "project_id",
            sa.UUID(as_uuid=True),
            sa.ForeignKey("projects.id", ondelete="CASCADE", name="fk_project_domain_verifications_project_id_projects"),
            nullable=False,
        ),
        sa.Column("domain", sa.String(length=253), nullable=False),
        sa.Column("verification_token", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column("verified_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_project_domain_verifications_project_id",
        "project_domain_verifications",
        ["project_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_project_domain_verifications_project_id", table_name="project_domain_verifications")
    op.drop_table("project_domain_verifications")
    op.drop_index("ix_projects_base_domain", table_name="projects")
    op.drop_index("ix_projects_owner_id", table_name="projects")
    op.drop_table("projects")
