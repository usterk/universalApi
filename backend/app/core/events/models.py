"""Database models for event persistence."""

from uuid import UUID

from sqlalchemy import String, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB

from app.core.database.base import Base, TimestampMixin, UUIDMixin


class SystemEvent(Base, UUIDMixin, TimestampMixin):
    """
    Persisted events for timeline and audit.

    Events are stored for historical queries and can be
    used for the timeline UI or audit logging.
    """

    __tablename__ = "system_events"

    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    source: Mapped[str] = mapped_column(String(200), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="info")
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)

    user_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=True,
    )

    # Indexes for timeline queries
    __table_args__ = (
        Index("idx_events_type_time", "event_type", "created_at"),
        Index("idx_events_source_time", "source", "created_at"),
        Index("idx_events_time", "created_at"),
        Index("idx_events_severity", "severity"),
    )

    def __repr__(self) -> str:
        return f"<SystemEvent {self.event_type} from {self.source}>"
