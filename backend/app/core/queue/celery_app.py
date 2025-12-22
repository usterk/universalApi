"""Celery application configuration."""

from celery import Celery

from app.config import settings
from app.core.logging import setup_logging

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

    # Graceful shutdown (Kubernetes-compatible)
    worker_shutdown_timeout=30,  # Match Kubernetes grace period
    worker_cancel_long_running_tasks_on_connection_loss=True,

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

# Initialize structured logging for Celery
setup_logging(
    log_level=settings.log_level,
    log_format=settings.log_format,
    is_development=settings.is_development,
    logs_dir=settings.logs_dir,
    log_to_file=settings.log_to_file,
    log_file_max_bytes=settings.log_file_max_bytes,
    log_file_backup_count=settings.log_file_backup_count,
    for_celery=True,
)
