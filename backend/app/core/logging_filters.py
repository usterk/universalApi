"""Logging filters for event routing.

This module provides filters to route events to separate log files while
maintaining dual logging (events appear in both event.log and backend.log).
"""

import logging


class EventFilter(logging.Filter):
    """Filter to capture only event-related logs.

    Events are identified by:
    - Logger name starting with "app.core.events"
    - Record having is_event=True attribute
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Return True only for event logs.

        Args:
            record: Log record to filter

        Returns:
            True if record is an event, False otherwise
        """
        return (
            record.name.startswith("app.core.events")
            or getattr(record, "is_event", False)
        )


class NonEventFilter(logging.Filter):
    """Filter to exclude event logs from main logs.

    This ensures backend.log doesn't contain events (they go to event.log).
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Return True for non-event logs.

        Args:
            record: Log record to filter

        Returns:
            True if record is NOT an event, False otherwise
        """
        return not (
            record.name.startswith("app.core.events")
            or getattr(record, "is_event", False)
        )
