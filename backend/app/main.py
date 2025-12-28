"""FastAPI application factory."""

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Annotated, AsyncGenerator
import time

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.database.session import engine, async_session_factory, get_db
from app.core.database.migration_check import require_migrations
from app.core.events.bus import EventBus, get_event_bus
from app.core.events.types import EventType, EventSeverity
from app.core.logging import setup_logging, get_logger, LoggingMiddleware
from app.core.plugins.registry import PluginRegistry
from app.core.plugins.loader import PluginLoader
from app.core.shutdown import get_shutdown_coordinator
from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifecycle management."""

    # === STARTUP ===
    # Initialize structured logging FIRST
    setup_logging(
        log_level=settings.log_level,
        log_format=settings.log_format,
        is_development=settings.is_development,
        logs_dir=settings.logs_dir,
        log_to_file=settings.log_to_file,
        log_file_max_bytes=settings.log_file_max_bytes,
        log_file_backup_count=settings.log_file_backup_count,
    )

    logger = get_logger(__name__)
    logger.info("application_starting", app_name=settings.app_name, environment=settings.app_env)

    # Check database migrations before starting
    try:
        await require_migrations(
            engine, fail_on_outdated=settings.require_migrations_on_startup
        )
    except RuntimeError as e:
        logger.error("migration_check_failed", error=str(e))
        raise  # Stop application startup

    # 1. Initialize shutdown coordinator
    shutdown_coordinator = get_shutdown_coordinator()
    shutdown_coordinator.setup_signal_handlers()

    # 2. Initialize core services
    event_bus = get_event_bus()
    event_bus.set_db_session_factory(async_session_factory)
    registry = PluginRegistry()

    # 3. Start Redis event subscriber (bridge Celery→EventBus→SSE)
    from app.core.events.redis_subscriber import RedisEventSubscriber

    redis_subscriber = RedisEventSubscriber(event_bus)
    subscriber_task = asyncio.create_task(redis_subscriber.start())
    logger.info("redis_subscriber_started")

    # 4. Load plugins
    loader = PluginLoader(registry, event_bus)
    discovered = loader.discover()
    logger.info("plugins_discovered", plugins=discovered)

    # Load plugin settings from database
    plugin_settings = await load_plugin_settings_from_db()
    logger.info(
        "plugin_settings_loaded",
        count=len(plugin_settings),
        plugins=list(plugin_settings.keys()),
    )
    await loader.load_all(plugin_settings)

    # 5. Mount plugin routers
    for plugin_name, router in registry.collect_routers():
        app.include_router(
            router,
            prefix=f"/api/v1/plugins/{plugin_name}",
            tags=[f"plugin:{plugin_name}"],
        )
        logger.info("plugin_router_mounted", plugin_name=plugin_name, prefix=f"/api/v1/plugins/{plugin_name}")

    # 6. Register event handlers from plugins
    for plugin in registry.get_active_plugins():
        handlers = plugin.get_event_handlers()
        for event_type, handler_list in handlers.items():
            for handler in handler_list:
                event_bus.subscribe(event_type, handler)

    # 7. Call startup hooks
    for plugin in registry.get_active_plugins():
        await plugin.on_startup()

    # 8. Store in app state
    app.state.event_bus = event_bus
    app.state.plugin_registry = registry
    app.state.shutdown_coordinator = shutdown_coordinator
    app.state.redis_subscriber = redis_subscriber

    logger.info(
        "application_started_successfully",
        app_name=settings.app_name,
        plugins_loaded=len(registry.get_active_plugins())
    )

    # 9. Emit system.startup event (using proper event type)
    await event_bus.emit(
        event_type=EventType.SYSTEM_STARTUP,
        source="system",
        payload={
            "app_name": settings.app_name,
            "environment": settings.app_env,
            "plugins_loaded": len(registry.get_active_plugins()),
            "plugin_names": [p.metadata.name for p in registry.get_active_plugins()],
        },
        severity=EventSeverity.SUCCESS,
        persist=True,
    )

    # Save application start time for uptime tracking
    app.state._start_time = time.time()

    yield

    # === SHUTDOWN ===
    shutdown_start = time.time()
    logger.info("application_shutting_down", app_name=settings.app_name)

    # 1. Emit system.shutdown event
    await event_bus.emit(
        event_type=EventType.SYSTEM_SHUTDOWN,
        source="system",
        payload={
            "app_name": settings.app_name,
            "uptime_seconds": time.time() - app.state._start_time,
            "reason": "graceful_shutdown",
        },
        severity=EventSeverity.WARNING,
        persist=True,
    )

    # 2. Stop accepting new tasks
    shutdown_coordinator.is_shutting_down = True
    logger.info("shutdown_blocking_new_tasks")

    # 3. Stop Redis subscriber
    redis_subscriber.stop()
    try:
        await asyncio.wait_for(subscriber_task, timeout=5.0)
        logger.info("redis_subscriber_stopped")
    except asyncio.TimeoutError:
        logger.warning("redis_subscriber_stop_timeout")
        subscriber_task.cancel()

    # 4. Wait for running jobs (with timeout)
    await _wait_for_running_jobs(event_bus, timeout=25)  # Leave 5s buffer

    # 5. Call plugin shutdown hooks
    for plugin in registry.get_active_plugins():
        try:
            await asyncio.wait_for(plugin.on_shutdown(), timeout=5.0)
        except asyncio.TimeoutError:
            logger.warning("plugin_shutdown_timeout", plugin_name=plugin.metadata.name)

    # 6. Close database connections
    await engine.dispose()

    elapsed = time.time() - shutdown_start
    logger.info(
        "application_shutdown_complete",
        app_name=settings.app_name,
        shutdown_duration_seconds=elapsed,
    )


async def load_plugin_settings_from_db() -> dict[str, dict]:
    """Load plugin settings from database.

    Returns:
        Dict mapping plugin_name to settings dict.
        Returns empty dict if no configs exist or on error.
    """
    from sqlalchemy import select
    from app.core.plugins.models import PluginConfig

    logger = get_logger(__name__)

    try:
        async with async_session_factory() as session:
            result = await session.execute(select(PluginConfig))
            configs = result.scalars().all()

            settings: dict[str, dict] = {}
            for config in configs:
                settings[config.plugin_name] = config.settings or {}

            logger.info(
                "plugin_settings_loaded_from_db",
                plugin_count=len(settings),
                plugins=list(settings.keys()),
            )
            return settings
    except Exception as e:
        logger.warning(
            "plugin_settings_load_failed",
            error=str(e),
            fallback="using_empty_settings",
        )
        return {}


async def _wait_for_running_jobs(event_bus: EventBus, timeout: int) -> None:
    """Wait for running jobs to complete with timeout.

    Args:
        event_bus: EventBus instance
        timeout: Maximum seconds to wait
    """
    from app.core.database.session import async_session_factory
    from app.core.plugins.models import ProcessingJob, JobStatus
    from sqlalchemy import select

    logger = get_logger(__name__)
    start_time = time.time()

    while time.time() - start_time < timeout:
        async with async_session_factory() as session:
            result = await session.execute(
                select(ProcessingJob).where(
                    ProcessingJob.status.in_([JobStatus.RUNNING.value, JobStatus.QUEUED.value])
                )
            )
            running_jobs = result.scalars().all()

            if not running_jobs:
                logger.info("shutdown_all_jobs_completed")
                return

            logger.info(
                "shutdown_waiting_for_jobs",
                running_count=len(running_jobs),
                remaining_timeout=timeout - (time.time() - start_time),
            )

        await asyncio.sleep(2)  # Check every 2 seconds

    # Timeout exceeded - cancel remaining jobs
    logger.warning("shutdown_timeout_cancelling_jobs")
    await _cancel_all_running_jobs(event_bus)


async def _cancel_all_running_jobs(event_bus: EventBus) -> None:
    """Cancel all running jobs during shutdown.

    Args:
        event_bus: EventBus instance
    """
    from app.core.database.session import async_session_factory
    from app.core.plugins.models import ProcessingJob, JobStatus
    from app.core.queue.celery_app import celery_app
    from sqlalchemy import select

    logger = get_logger(__name__)

    async with async_session_factory() as session:
        result = await session.execute(
            select(ProcessingJob).where(
                ProcessingJob.status.in_([JobStatus.RUNNING.value, JobStatus.QUEUED.value])
            )
        )
        running_jobs = result.scalars().all()

        for job in running_jobs:
            # Revoke Celery task
            if job.task_id:
                celery_app.control.revoke(job.task_id, terminate=True)

            # Update job status
            job.status = JobStatus.CANCELLED.value
            job.completed_at = datetime.utcnow()
            job.error_message = "Cancelled due to system shutdown"

            # Emit cancelled event
            await event_bus.emit(
                event_type=EventType.JOB_CANCELLED,
                source="system:shutdown",
                payload={
                    "job_id": str(job.id),
                    "plugin_name": job.plugin_name,
                    "document_id": str(job.document_id),
                    "reason": "system_shutdown",
                },
                severity=EventSeverity.WARNING,
                persist=True,
            )

        await session.commit()
        logger.info("shutdown_cancelled_jobs", count=len(running_jobs))


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Universal API for data processing with plugin architecture",
        lifespan=lifespan,
        docs_url="/api/docs" if settings.debug else None,
        redoc_url="/api/redoc" if settings.debug else None,
        openapi_url="/api/openapi.json" if settings.debug else None,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Logging middleware (adds correlation IDs and request context)
    app.add_middleware(LoggingMiddleware)

    # Core API routes
    app.include_router(api_router, prefix="/api/v1")

    @app.get("/health")
    async def health_check(
        db: Annotated[AsyncSession, Depends(get_db)],
        event_bus: Annotated[EventBus, Depends(get_event_bus)],
    ) -> dict:
        """
        Comprehensive health check endpoint - NO AUTH REQUIRED.

        Emits events for timeline visibility.
        Returns: plugins, database, Redis, Celery status.
        """
        import logging
        from uuid import uuid4

        logger = logging.getLogger(__name__)
        check_id = str(uuid4())
        start_time = time.time()

        # Emit started event as a proper system event
        await event_bus.emit(
            event_type=EventType.SYSTEM_HEALTH_CHECK_STARTED,
            source="system:health_check",
            payload={
                "activity_id": check_id,
                "activity_type": "health_check",
                "activity_name": "System Health Check",
                "activity_color": "#22C55E",
                "started_at": datetime.utcnow().isoformat() + "Z",
            },
            severity=EventSeverity.INFO,
            persist=False,  # Don't clutter database
        )

        # 1. Get plugin status
        registry = app.state.plugin_registry
        plugins_data = []
        active_plugins = registry.get_active_plugins()
        for plugin in registry.plugins.values():
            plugins_data.append({
                "name": plugin.metadata.name,
                "display_name": plugin.metadata.display_name,
                "version": plugin.metadata.version,
                "status": "enabled" if plugin in active_plugins else "disabled",
                "priority": plugin.metadata.priority,
            })

        # 2. Database ping test
        db_status = "unknown"
        db_latency = None
        try:
            db_start = time.time()
            await db.execute(text("SELECT 1"))
            db_latency = round((time.time() - db_start) * 1000, 2)
            db_status = "connected"
        except Exception as e:
            db_status = "error"
            logger.error(f"Database health check failed: {e}")

        # 3. Redis ping test
        redis_status = "unknown"
        redis_latency = None
        try:
            import redis.asyncio as redis
            redis_start = time.time()
            r = redis.from_url(settings.redis_url)
            await r.ping()
            redis_latency = round((time.time() - redis_start) * 1000, 2)
            redis_status = "connected"
            await r.close()
        except Exception as e:
            redis_status = "error"
            logger.error(f"Redis health check failed: {e}")

        # 4. Celery worker check
        celery_status = "unknown"
        celery_workers = 0
        try:
            from app.core.queue.celery_app import celery_app
            inspect = celery_app.control.inspect()
            active = inspect.active()
            celery_workers = len(active) if active else 0
            celery_status = "available" if celery_workers > 0 else "no_workers"
        except Exception as e:
            celery_status = "error"
            logger.error(f"Celery health check failed: {e}")

        # 5. Calculate uptime
        if not hasattr(app.state, '_start_time'):
            app.state._start_time = time.time()
        uptime = round(time.time() - app.state._start_time, 2)

        # Overall status
        overall_status = "healthy"
        if db_status == "error" or redis_status == "error":
            overall_status = "degraded"
        if celery_status == "error" or celery_status == "no_workers":
            overall_status = "degraded"

        response = {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "uptime_seconds": uptime,
            "version": "0.1.0",
            "environment": settings.app_env,
            "database": {
                "status": db_status,
                "latency_ms": db_latency,
            },
            "redis": {
                "status": redis_status,
                "latency_ms": redis_latency,
            },
            "celery": {
                "status": celery_status,
                "active_workers": celery_workers,
            },
            "plugins": plugins_data,
        }

        # Emit completed event as a proper system event
        elapsed_ms = round((time.time() - start_time) * 1000, 2)
        await event_bus.emit(
            event_type=EventType.SYSTEM_HEALTH_CHECK_COMPLETED,
            source="system:health_check",
            payload={
                "activity_id": check_id,
                "activity_type": "health_check",
                "activity_name": "System Health Check",
                "activity_color": "#22C55E",
                "duration_ms": elapsed_ms,
                "status": overall_status,
                "completed_at": datetime.utcnow().isoformat() + "Z",
                "database_status": db_status,
                "redis_status": redis_status,
                "celery_status": celery_status,
            },
            severity=EventSeverity.SUCCESS if overall_status == "healthy" else EventSeverity.WARNING,
            persist=False,
        )

        return response

    return app


app = create_app()
