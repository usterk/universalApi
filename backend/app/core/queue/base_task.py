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
        plugin_name = self.name.split(".")[0] if "." in self.name else self.name

        payload = {
            "task_id": task_id,
            "job_id": str(job_id) if job_id else None,
            "plugin_name": plugin_name,
            "result_summary": str(retval)[:200] if retval else None,
            "completed_at": datetime.utcnow().isoformat(),
        }

        # Add result details if available
        if isinstance(retval, dict):
            payload.update(
                {
                    "status": retval.get("status"),
                    "duration_seconds": retval.get("processing_time_seconds"),
                }
            )

        self.event_bus.emit_sync(
            event_type=EventType.JOB_COMPLETED,
            source=f"task:{self.name}",
            payload=payload,
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
        plugin_name = self.name.split(".")[0] if "." in self.name else self.name

        self.event_bus.emit_sync(
            event_type=EventType.JOB_FAILED,
            source=f"task:{self.name}",
            payload={
                "task_id": task_id,
                "job_id": str(job_id) if job_id else None,
                "plugin_name": plugin_name,
                "error": str(exc),
                "error_type": type(exc).__name__,
                "failed_at": datetime.utcnow().isoformat(),
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

    def emit_started(self, job_id: str, document_id: str | None = None, **extra) -> None:
        """Emit job started event with rich payload."""
        plugin_name = self.name.split(".")[0] if "." in self.name else self.name

        payload = {
            "job_id": job_id,
            "document_id": document_id,
            "plugin_name": plugin_name,
            "timestamp": datetime.utcnow().isoformat(),
            **extra,
        }

        self.event_bus.emit_sync(
            event_type=EventType.JOB_STARTED,
            source=f"task:{self.name}",
            payload=payload,
        )

    def check_cancellation(self, job_id: str) -> None:
        """Check if job has been cancelled and raise if so.

        Args:
            job_id: Job ID to check

        Raises:
            CancelledException: If job has been cancelled
        """
        from app.core.database.session import async_session_factory
        from app.core.plugins.models import ProcessingJob, JobStatus
        from sqlalchemy import select
        import asyncio

        async def _check():
            async with async_session_factory() as session:
                result = await session.execute(
                    select(ProcessingJob).where(ProcessingJob.id == job_id)
                )
                job = result.scalar_one_or_none()

                if job and job.status == JobStatus.CANCELLED.value:
                    raise CancelledException(f"Job {job_id} was cancelled")

        # Run async check in sync context
        loop = asyncio.new_event_loop()
        try:
            loop.run_until_complete(_check())
        finally:
            loop.close()


class CancelledException(Exception):
    """Exception raised when job is cancelled."""

    pass
