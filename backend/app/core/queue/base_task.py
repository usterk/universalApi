"""Base task class for plugins with event emission."""

from celery import Task
from datetime import datetime
from typing import Any

from app.core.events.bus import get_event_bus
from app.core.events.types import EventType


class PluginTask(Task):
    """
    Base class for plugin Celery tasks.
    Automatically emits events on state changes.
    """

    abstract = True
    _event_bus = None

    @property
    def event_bus(self):
        if self._event_bus is None:
            self._event_bus = get_event_bus()
        return self._event_bus

    def on_success(self, retval: Any, task_id: str, args: tuple, kwargs: dict) -> None:
        """Called on task success."""
        job_id = args[0] if args else kwargs.get("job_id")

        self.event_bus.emit_sync(
            event_type=EventType.JOB_COMPLETED,
            source=f"task:{self.name}",
            payload={
                "task_id": task_id,
                "job_id": str(job_id) if job_id else None,
                "result_summary": str(retval)[:200] if retval else None,
            },
        )

    def on_failure(
        self,
        exc: Exception,
        task_id: str,
        args: tuple,
        kwargs: dict,
        einfo: Any,
    ) -> None:
        """Called on task failure."""
        job_id = args[0] if args else kwargs.get("job_id")

        self.event_bus.emit_sync(
            event_type=EventType.JOB_FAILED,
            source=f"task:{self.name}",
            payload={
                "task_id": task_id,
                "job_id": str(job_id) if job_id else None,
                "error": str(exc),
            },
        )

    def update_progress(
        self,
        job_id: str,
        progress: int,
        message: str = "",
    ) -> None:
        """Helper to update job progress."""
        self.event_bus.emit_sync(
            event_type=EventType.JOB_PROGRESS,
            source=f"task:{self.name}",
            payload={
                "job_id": job_id,
                "progress": progress,
                "message": message,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    def emit_started(self, job_id: str, document_id: str | None = None) -> None:
        """Emit job started event."""
        self.event_bus.emit_sync(
            event_type=EventType.JOB_STARTED,
            source=f"task:{self.name}",
            payload={
                "job_id": job_id,
                "document_id": document_id,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
