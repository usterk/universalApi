"""Structured logging configuration using structlog.

This module provides a unified logging setup for the UniversalAPI application.
- Development: Human-readable colored console output
- Production: JSON formatted output for log aggregation

Usage:
    from app.core.logging import setup_logging, get_logger

    # Initialize at app startup
    setup_logging()

    # Get a logger
    logger = get_logger(__name__)
    logger.info("event_name", key="value")
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

import structlog
from structlog.types import Processor


def get_log_level(level_name: str) -> int:
    """Convert log level name to logging constant."""
    levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    return levels.get(level_name.upper(), logging.INFO)


def setup_logging(
    log_level: str = "INFO",
    log_format: str = "auto",
    is_development: bool = True,
    logs_dir: str | None = None,
    log_to_file: bool = False,
    log_file_max_bytes: int = 10 * 1024 * 1024,
    log_file_backup_count: int = 5,
    for_celery: bool = False,
) -> None:
    """
    Configure structured logging for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Output format - 'auto' (based on environment), 'console', or 'json'
        is_development: Whether running in development mode
        logs_dir: Directory for log files (if log_to_file is True)
        log_to_file: Whether to also write logs to files
        log_file_max_bytes: Max size of each log file before rotation
        log_file_backup_count: Number of backup files to keep
    """
    level = get_log_level(log_level)

    # Determine format based on settings
    if log_format == "auto":
        use_json = not is_development
    else:
        use_json = log_format == "json"

    # Shared processors for all environments
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    # Configure structlog
    structlog.configure(
        processors=shared_processors + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Create formatter based on environment
    if use_json:
        formatter = structlog.stdlib.ProcessorFormatter(
            processor=structlog.processors.JSONRenderer(),
            foreign_pre_chain=shared_processors,
        )
    else:
        formatter = structlog.stdlib.ProcessorFormatter(
            processor=structlog.dev.ConsoleRenderer(
                colors=True,
                exception_formatter=structlog.dev.plain_traceback,
            ),
            foreign_pre_chain=shared_processors,
        )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers
    root_logger.handlers = []

    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(level)
    root_logger.addHandler(console_handler)

    # Add file handler if configured
    if log_to_file and logs_dir:
        _add_file_handler(
            root_logger,
            logs_dir=logs_dir,
            level=level,
            max_bytes=log_file_max_bytes,
            backup_count=log_file_backup_count,
        )
        # Add separate event log handler
        _add_event_log_handler(
            root_logger,
            logs_dir=logs_dir,
            level=level,
            max_bytes=log_file_max_bytes,
            backup_count=log_file_backup_count,
        )

    # Reduce noise from common libraries
    _configure_library_loggers(level)

    # Configure Celery loggers if requested
    if for_celery:
        _configure_celery_loggers(root_logger, formatter, level)


def _add_file_handler(
    logger: logging.Logger,
    logs_dir: str,
    level: int,
    max_bytes: int,
    backup_count: int,
) -> None:
    """Add rotating file handler with JSON format (excludes events)."""
    from app.core.logging_filters import NonEventFilter

    log_path = Path(logs_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # JSON formatter for file logs (always JSON for machine parsing)
    json_formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.processors.JSONRenderer(),
        foreign_pre_chain=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
        ],
    )

    file_handler = RotatingFileHandler(
        log_path / "backend.log",
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setFormatter(json_formatter)
    file_handler.setLevel(level)
    file_handler.addFilter(NonEventFilter())  # Exclude events
    logger.addHandler(file_handler)


def _add_event_log_handler(
    logger: logging.Logger,
    logs_dir: str,
    level: int,
    max_bytes: int,
    backup_count: int,
) -> None:
    """Add separate rotating file handler for events only."""
    from app.core.logging_filters import EventFilter

    log_path = Path(logs_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # JSON formatter for event logs (always JSON for machine parsing)
    json_formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.processors.JSONRenderer(),
        foreign_pre_chain=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
        ],
    )

    # Event-specific file handler
    event_handler = RotatingFileHandler(
        log_path / "event.log",
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    event_handler.setFormatter(json_formatter)
    event_handler.setLevel(level)
    event_handler.addFilter(EventFilter())  # Only events
    logger.addHandler(event_handler)


def _configure_library_loggers(app_level: int) -> None:
    """Set appropriate log levels for third-party libraries."""
    # These libraries are often too verbose at INFO level
    noisy_loggers = [
        "uvicorn.access",
        "uvicorn.error",
        "sqlalchemy.engine",
        "sqlalchemy.pool",
        "httpx",
        "httpcore",
        "celery",
        "celery.worker",
        "celery.app.trace",
        "asyncio",
        "aiohttp",
    ]

    # Set minimum level for noisy loggers
    min_level = max(logging.WARNING, app_level)

    for logger_name in noisy_loggers:
        logging.getLogger(logger_name).setLevel(min_level)

    # uvicorn.error should always show errors
    logging.getLogger("uvicorn.error").setLevel(logging.ERROR)


def _configure_celery_loggers(
    root_logger: logging.Logger,
    formatter: logging.Formatter,
    level: int,
) -> None:
    """Configure Celery-specific loggers to use structlog."""
    celery_loggers = [
        "celery",
        "celery.worker",
        "celery.task",
        "celery.app.trace",
        "celery.beat",
    ]

    for logger_name in celery_loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(level)
        logger.handlers = []  # Remove existing handlers
        logger.propagate = True  # Propagate to root logger with structlog


def get_logger(name: str = __name__) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (typically __name__ of the calling module)

    Returns:
        A bound logger instance with structured logging capabilities

    Example:
        logger = get_logger(__name__)
        logger.info("user_created", user_id="123", email="user@example.com")
        logger.error("database_error", error=str(e), query="SELECT ...")
    """
    return structlog.stdlib.get_logger(name)


class LoggingMiddleware:
    """
    ASGI middleware for request logging.

    Adds correlation ID and request context to all logs within a request.
    Skips logging for health check endpoints.
    """

    SKIP_PATHS = {"/health", "/api/v1/health", "/metrics"}

    def __init__(self, app: Any) -> None:
        self.app = app
        self.logger = get_logger("http")

    async def __call__(self, scope: dict, receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")

        # Skip logging for health checks
        if path in self.SKIP_PATHS:
            await self.app(scope, receive, send)
            return

        # Generate correlation ID
        import uuid
        correlation_id = str(uuid.uuid4())[:8]

        # Bind context for all logs in this request
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            correlation_id=correlation_id,
            path=path,
            method=scope.get("method", ""),
        )

        # Track response status
        status_code = 500

        async def send_wrapper(message: dict) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message.get("status", 500)
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            # Log completed request
            log_method = self.logger.info if status_code < 400 else self.logger.warning
            log_method(
                "request_completed",
                status_code=status_code,
            )
            structlog.contextvars.clear_contextvars()
