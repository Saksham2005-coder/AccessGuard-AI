"""Project domain DNS ownership verification persistence model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import TIMESTAMP, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.project import Project


class ProjectDomainVerification(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """DNS TXT token verification records validating domain control."""

    __tablename__ = "project_domain_verifications"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    domain: Mapped[str] = mapped_column(
        String(253),
        nullable=False,
    )
    verification_token: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
    )  # pending, verified, expired
    verified_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )
    expires_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=False,
    )

    # Relationships
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="verifications",
    )
