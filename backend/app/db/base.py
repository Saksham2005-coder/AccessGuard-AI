"""SQLAlchemy Declarative Base and common model mixins."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import TIMESTAMP, MetaData
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Standard naming conventions for constraints and indexes
POSTGRES_NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


def utc_now() -> datetime:
    """Return timezone-aware current UTC timestamp."""
    return datetime.now(UTC)


def ensure_utc(dt: datetime) -> datetime:
    """Ensure a datetime instance is timezone-aware in UTC."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)


class Base(DeclarativeBase):
    """Base declarative class for all AccessGuard SQLAlchemy models."""

    metadata = MetaData(naming_convention=POSTGRES_NAMING_CONVENTION)


class UUIDPrimaryKeyMixin:
    """Mixin providing UUID primary key."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )


class TimestampMixin:
    """Mixin providing created_at and updated_at timezone-aware timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=utc_now,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        default=utc_now,
        onupdate=utc_now,
        nullable=False,
    )
