"""Project persistence model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import TIMESTAMP, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.domain_verification import ProjectDomainVerification
    from app.db.models.user import User


class Project(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """User-owned web auditing project entity."""

    __tablename__ = "projects"

    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(160),
        nullable=False,
    )
    base_domain: Mapped[str] = mapped_column(
        String(253),
        index=True,
        nullable=False,
    )
    archived_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
    )

    # Relationships
    owner: Mapped["User"] = relationship("User")
    verifications: Mapped[list["ProjectDomainVerification"]] = relationship(
        "ProjectDomainVerification",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="desc(ProjectDomainVerification.created_at)",
    )
