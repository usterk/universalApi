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
        """Called on task success - update ProcessingJob status."""
        from uuid import UUID
        from app.core.plugins.models import ProcessingJob, JobStatus
        from sqlalchemy import create_engine, select
        from sqlalchemy.orm import sessionmaker
        from app.config import settings

        job_id = args[0] if args else kwargs.get("job_id")
        plugin_name = self.name.split(".")[0] if "." in self.name else self.name

        # Update ProcessingJob record in database
        if job_id:
            # Import all models to register them with SQLAlchemy
            from app.core.users.models import User  # noqa: F401
            from app.core.documents.models import Document  # noqa: F401
            from app.core.sources.models import Source  # noqa: F401

            engine = create_engine(settings.database_url_sync)
            SessionLocal = sessionmaker(bind=engine)
            session = SessionLocal()
            try:
                result = session.execute(
                    select(ProcessingJob).where(
                        ProcessingJob.document_id == UUID(job_id),
                        ProcessingJob.plugin_name == plugin_name
                    ).order_by(ProcessingJob.created_at.desc())
                )
                processing_job = result.scalars().first()
                if processing_job:
                    processing_job.status = JobStatus.COMPLETED.value
                    processing_job.progress = 100
                    processing_job.progress_message = "Completed"
                    processing_job.completed_at = datetime.utcnow()
                    session.commit()
            finally:
                session.close()

        payload = {
            "task_id": task_id,
            "job_id": str(job_id) if job_id else None,
            "plugin_name": plugin_name,
            "result_summary": str(retval)[:200] if retval else None,
            "completed_at": datetime.utcnow().isoformat() + "Z",
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
        """Called on task failure - update ProcessingJob status."""
        from uuid import UUID
        from app.core.plugins.models import ProcessingJob, JobStatus
        from sqlalchemy import create_engine, select
        from sqlalchemy.orm import sessionmaker
        from app.config import settings

        job_id = args[0] if args else kwargs.get("job_id")
        plugin_name = self.name.split(".")[0] if "." in self.name else self.name

        # Update ProcessingJob record in database
        if job_id:
            # Import all models to register them with SQLAlchemy
            from app.core.users.models import User  # noqa: F401
            from app.core.documents.models import Document  # noqa: F401
            from app.core.sources.models import Source  # noqa: F401

            engine = create_engine(settings.database_url_sync)
            SessionLocal = sessionmaker(bind=engine)
            session = SessionLocal()
            try:
                result = session.execute(
                    select(ProcessingJob).where(
                        ProcessingJob.document_id == UUID(job_id),
                        ProcessingJob.plugin_name == plugin_name
                    ).order_by(ProcessingJob.created_at.desc())
                )
                processing_job = result.scalars().first()
                if processing_job:
                    processing_job.status = JobStatus.FAILED.value
                    processing_job.error_message = str(exc)
                    processing_job.completed_at = datetime.utcnow()
                    session.commit()
            finally:
                session.close()

        self.event_bus.emit_sync(
            event_type=EventType.JOB_FAILED,
            source=f"task:{self.name}",
            payload={
                "task_id": task_id,
                "job_id": str(job_id) if job_id else None,
                "plugin_name": plugin_name,
                "error": str(exc),
                "error_type": type(exc).__name__,
                "failed_at": datetime.utcnow().isoformat() + "Z",
            },
        )

    def update_progress(
        self,
        job_id: str,
        progress: int,
        message: str = "",
    ) -> None:
        """Helper to update job progress and ProcessingJob record."""
        from uuid import UUID
        from app.core.plugins.models import ProcessingJob
        from sqlalchemy import create_engine, select
        from sqlalchemy.orm import sessionmaker
        from app.config import settings

        plugin_name = self.name.split(".")[0] if "." in self.name else self.name

        # Update ProcessingJob record in database
        # Import all models to register them with SQLAlchemy
        from app.core.users.models import User  # noqa: F401
        from app.core.documents.models import Document  # noqa: F401
        from app.core.sources.models import Source  # noqa: F401

        engine = create_engine(settings.database_url_sync)
        SessionLocal = sessionmaker(bind=engine)
        session = SessionLocal()
        try:
            result = session.execute(
                select(ProcessingJob).where(
                    ProcessingJob.document_id == UUID(job_id),
                    ProcessingJob.plugin_name == plugin_name
                ).order_by(ProcessingJob.created_at.desc())
            )
            processing_job = result.scalars().first()
            if processing_job:
                processing_job.progress = progress
                processing_job.progress_message = message
                session.commit()
        finally:
            session.close()

        self.event_bus.emit_sync(
            event_type=EventType.JOB_PROGRESS,
            source=f"task:{self.name}",
            payload={
                "job_id": job_id,
                "progress": progress,
                "message": message,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            },
        )

    def emit_started(self, job_id: str, document_id: str | None = None, **extra) -> None:
        """Emit job started event with rich payload and create ProcessingJob record."""
        from uuid import UUID
        from app.core.plugins.models import ProcessingJob, JobStatus
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
        from app.config import settings

        plugin_name = self.name.split(".")[0] if "." in self.name else self.name

        payload = {
            "job_id": job_id,
            "document_id": document_id,
            "plugin_name": plugin_name,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            **extra,
        }

        # Create ProcessingJob record in database
        if document_id:
            # Import all models to register them with SQLAlchemy
            from app.core.users.models import User  # noqa: F401
            from app.core.documents.models import Document  # noqa: F401
            from app.core.sources.models import Source  # noqa: F401

            engine = create_engine(settings.database_url_sync)
            SessionLocal = sessionmaker(bind=engine)
            session = SessionLocal()
            try:
                processing_job = ProcessingJob(
                    document_id=UUID(document_id),
                    plugin_name=plugin_name,
                    status=JobStatus.RUNNING.value,
                    progress=0,
                    progress_message="Started",
                    started_at=datetime.utcnow(),
                )
                session.add(processing_job)
                session.commit()
            finally:
                session.close()

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
