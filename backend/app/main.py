"""FastAPI application factory."""

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
from app.core.events.bus import EventBus, get_event_bus
from app.core.events.types import EventSeverity
from app.core.plugins.registry import PluginRegistry
from app.core.plugins.loader import PluginLoader
from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifecycle management."""

    # === STARTUP ===
    print(f"Starting {settings.app_name}...")

    # 1. Initialize core services
    event_bus = get_event_bus()
    event_bus.set_db_session_factory(async_session_factory)
    registry = PluginRegistry()

    # 2. Load plugins
    loader = PluginLoader(registry, event_bus)
    discovered = loader.discover()
    print(f"Discovered plugins: {discovered}")

    # Load plugin settings (from DB or defaults)
    plugin_settings: dict[str, dict] = {}  # TODO: Load from DB
    await loader.load_all(plugin_settings)

    # 3. Mount plugin routers
    for plugin_name, router in registry.collect_routers():
        app.include_router(
            router,
            prefix=f"/api/v1/plugins/{plugin_name}",
            tags=[f"plugin:{plugin_name}"],
        )
        print(f"Mounted plugin router: /api/v1/plugins/{plugin_name}")

    # 4. Register event handlers from plugins
    for plugin in registry.get_active_plugins():
        handlers = plugin.get_event_handlers()
        for event_type, handler_list in handlers.items():
            for handler in handler_list:
                event_bus.subscribe(event_type, handler)

    # 5. Call startup hooks
    for plugin in registry.get_active_plugins():
        await plugin.on_startup()

    # Store in app state
    app.state.event_bus = event_bus
    app.state.plugin_registry = registry

    print(f"{settings.app_name} started successfully!")

    # Emit startup event as a "job" so it appears on timeline
    await event_bus.emit(
        event_type="job.completed",
        source="system:startup",
        payload={
            "job_id": "startup",
            "plugin_name": "system",
            "plugin_color": "#10B981",
            "document_id": "system",
            "document_name": "Application Startup",
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat(),
            "app_name": settings.app_name,
            "environment": settings.app_env,
            "plugins_loaded": len(registry.get_active_plugins()),
        },
        severity=EventSeverity.SUCCESS,
        persist=False,
    )
    print(f"Emitted startup event for SSE stream")

    # Save application start time for uptime tracking
    app.state._start_time = time.time()

    yield

    # === SHUTDOWN ===
    print(f"Shutting down {settings.app_name}...")

    for plugin in registry.get_active_plugins():
        await plugin.on_shutdown()

    # Close database connections
    await engine.dispose()

    print(f"{settings.app_name} shut down complete.")


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

        # Emit started event as a job event (for timeline visibility)
        await event_bus.emit(
            event_type="job.started",
            source="system:health_check",
            payload={
                "job_id": check_id,
                "plugin_name": "health_check",
                "plugin_color": "#22C55E",
                "document_id": "health",
                "document_name": "System Health Check",
                "started_at": datetime.utcnow().isoformat(),
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
            "timestamp": datetime.utcnow().isoformat(),
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

        # Emit completed event as a job event (for timeline visibility)
        elapsed_ms = round((time.time() - start_time) * 1000, 2)
        await event_bus.emit(
            event_type="job.completed",
            source="system:health_check",
            payload={
                "job_id": check_id,
                "plugin_name": "health_check",
                "plugin_color": "#22C55E",
                "document_id": "health",
                "document_name": "System Health Check",
                "duration_ms": elapsed_ms,
                "status": overall_status,
                "completed_at": datetime.utcnow().isoformat(),
            },
            severity=EventSeverity.SUCCESS if overall_status == "healthy" else EventSeverity.WARNING,
            persist=False,
        )

        return response

    return app


app = create_app()
