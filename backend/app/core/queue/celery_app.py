"""Celery application configuration."""

from celery import Celery

from app.config import settings

celery_app = Celery(
    "universalapi",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Task tracking
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
    task_soft_time_limit=3300,  # 55 min soft limit

    # Result settings
    result_expires=86400,  # 24 hours

    # Worker settings
    worker_prefetch_multiplier=1,  # Fair distribution
    worker_concurrency=4,

    # Task routing - each plugin gets its own queue
    task_routes={
        "plugins.upload.*": {"queue": "upload"},
        "plugins.audio_transcription.*": {"queue": "transcription"},
        "plugins.content_analyzer.*": {"queue": "analyzer"},
        "plugins.lie_detection.*": {"queue": "detection"},
        "plugins.search.*": {"queue": "search"},
    },

    # Default queue
    task_default_queue="default",
)

# Auto-discover tasks from plugins
celery_app.autodiscover_tasks(["plugins"])
