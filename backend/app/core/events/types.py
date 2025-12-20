"""Event types and models."""

from datetime import datetime
from enum import Enum
from uuid import UUID, uuid4
from typing import Any

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Core event types in the system."""

    # Document events
    DOCUMENT_CREATED = "document.created"
    DOCUMENT_UPDATED = "document.updated"
    DOCUMENT_DELETED = "document.deleted"

    # Job events
    JOB_QUEUED = "job.queued"
    JOB_STARTED = "job.started"
    JOB_PROGRESS = "job.progress"
    JOB_COMPLETED = "job.completed"
    JOB_FAILED = "job.failed"
    JOB_CANCELLED = "job.cancelled"

    # User events
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_CREATED = "user.created"

    # Source events
    SOURCE_CREATED = "source.created"
    SOURCE_DELETED = "source.deleted"

    # Plugin events
    PLUGIN_LOADED = "plugin.loaded"
    PLUGIN_ENABLED = "plugin.enabled"
    PLUGIN_DISABLED = "plugin.disabled"
    PLUGIN_ERROR = "plugin.error"

    # System events
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"

    # Custom (plugins can define their own)
    CUSTOM = "custom"


class EventSeverity(str, Enum):
    """Event severity for timeline visualization."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    SUCCESS = "success"


class Event(BaseModel):
    """Event model for the event bus."""

    id: UUID = Field(default_factory=uuid4)
    type: str  # Event type string (can be EventType or custom)
    source: str  # Origin: "core:auth", "plugin:transcription", "job:process_audio"
    payload: dict[str, Any] = Field(default_factory=dict)
    severity: EventSeverity = EventSeverity.INFO
    user_id: UUID | None = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    model_config = {
        "json_encoders": {
            datetime: lambda v: v.isoformat(),
            UUID: str,
        }
    }


class TimelineEvent(BaseModel):
    """Event model specifically for timeline visualization."""

    job_id: UUID
    plugin_name: str
    plugin_color: str  # Hex color
    event_type: str
    document_id: UUID
    document_name: str
    progress: int = 0  # 0-100
    progress_message: str = ""
    started_at: datetime
    ended_at: datetime | None = None
    error: str | None = None
