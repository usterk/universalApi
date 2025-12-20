"""Database models for plugin system."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from sqlalchemy import String, Integer, Boolean, ForeignKey, Index, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID, JSONB, ARRAY

from app.core.database.base import Base, TimestampMixin, UUIDMixin


class PluginConfig(Base, UUIDMixin, TimestampMixin):
    """Plugin configuration stored in database."""

    __tablename__ = "plugin_configs"

    plugin_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    settings: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Cached metadata from plugin
    display_name: Mapped[str | None] = mapped_column(String(255))
    version: Mapped[str | None] = mapped_column(String(50))
    priority: Mapped[int] = mapped_column(Integer, default=100)
    max_concurrent_jobs: Mapped[int] = mapped_column(Integer, default=5)

    def __repr__(self) -> str:
        return f"<PluginConfig {self.plugin_name}>"


class FilterType(str, Enum):
    """Types of plugin filters."""

    OWNER = "owner"
    SOURCE = "source"
    DOCUMENT_TYPE = "document_type"
    CUSTOM = "custom"


class FilterOperator(str, Enum):
    """Filter operators."""

    INCLUDE = "include"
    EXCLUDE = "exclude"


class PluginFilter(Base, UUIDMixin, TimestampMixin):
    """
    Filter rules for plugin processing.

    Determines which documents a plugin should process.
    """

    __tablename__ = "plugin_filters"

    plugin_name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    filter_type: Mapped[str] = mapped_column(String(50), nullable=False)
    operator: Mapped[str] = mapped_column(String(20), nullable=False)
    value: Mapped[str] = mapped_column(String(500), nullable=False)  # ID or JSON

    # Indexes
    __table_args__ = (Index("idx_plugin_filters_plugin", "plugin_name"),)

    def __repr__(self) -> str:
        return f"<PluginFilter {self.plugin_name} {self.filter_type}:{self.operator}>"


class JobStatus(str, Enum):
    """Processing job status."""

    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProcessingJob(Base, UUIDMixin, TimestampMixin):
    """Processing job for document handling."""

    __tablename__ = "processing_jobs"

    document_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents.id"),
        nullable=False,
    )

    plugin_name: Mapped[str] = mapped_column(String(100), nullable=False)
    task_id: Mapped[str | None] = mapped_column(String(100))  # Celery task ID

    status: Mapped[str] = mapped_column(String(20), default=JobStatus.PENDING.value)
    progress: Mapped[int] = mapped_column(Integer, default=0)  # 0-100
    progress_message: Mapped[str | None] = mapped_column(String(500))

    result: Mapped[dict | None] = mapped_column(JSONB)
    error_message: Mapped[str | None] = mapped_column(String(2000))

    # Output document (if plugin creates new document)
    output_document_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("documents.id"),
        nullable=True,
    )

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Relationships
    document: Mapped["Document"] = relationship(foreign_keys=[document_id])
    output_document: Mapped["Document | None"] = relationship(foreign_keys=[output_document_id])

    # Indexes
    __table_args__ = (
        Index("idx_jobs_document", "document_id"),
        Index("idx_jobs_plugin", "plugin_name"),
        Index("idx_jobs_status", "status"),
        Index("idx_jobs_created", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<ProcessingJob {self.id} {self.plugin_name}:{self.status}>"


# Import Document for type hints
from app.core.documents.models import Document  # noqa: E402
