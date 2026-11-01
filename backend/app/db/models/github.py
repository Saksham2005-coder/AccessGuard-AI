"""GitHub PR integration models.

Phase 19 Feature 7: GitHub repository linking, HMAC-verified webhook processing,
PR review tracking, and comment record persistence.
"""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.project import Project
    from app.db.models.scan import Scan
    from app.db.models.user import User


class GitHubIntegration(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Configuration linking an AccessGuard project to a GitHub repository."""

    __tablename__ = "github_integrations"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        unique=True,
        index=True,
        nullable=False,
    )
    repo_owner: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    repo_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    installation_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    webhook_secret: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    access_token: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    target_branch: Mapped[str] = mapped_column(
        String(100),
        default="main",
        nullable=False,
    )
    enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    auto_review_prs: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project")
    user: Mapped["User"] = relationship("User")
    reviews: Mapped[list["GitHubReviewRecord"]] = relationship(
        "GitHubReviewRecord",
        back_populates="integration",
        cascade="all, delete-orphan",
    )


class GitHubReviewRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Historical record of an accessibility review generated for a GitHub pull request."""

    __tablename__ = "github_review_records"

    integration_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("github_integrations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    delivery_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )
    pr_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    pr_title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    pr_author: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    head_sha: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    base_sha: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    scan_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scans.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="received",
        nullable=False,
    )
    comment_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    summary_markdown: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    integration: Mapped["GitHubIntegration"] = relationship(
        "GitHubIntegration", back_populates="reviews"
    )
    project: Mapped["Project"] = relationship("Project")
    scan: Mapped["Scan | None"] = relationship("Scan")
