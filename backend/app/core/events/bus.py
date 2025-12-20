"""Event Bus implementation with SSE support."""

import asyncio
import json
import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Callable
from uuid import UUID

from app.core.events.types import Event, EventType, EventSeverity
from app.core.events.models import SystemEvent

logger = logging.getLogger(__name__)


class EventBus:
    """
    Central event bus with:
    - Pub/sub for handlers
    - Buffer for recent events (SSE)
    - Persistence to database
    - Multiple subscriber support
    """

    _instance: "EventBus | None" = None

    def __new__(cls) -> "EventBus":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._subscribers: dict[str, list[Callable]] = defaultdict(list)
            cls._instance._sse_clients: set[asyncio.Queue] = set()
            cls._instance._event_buffer: list[Event] = []
            cls._instance._buffer_max_size = 1000
            cls._instance._buffer_max_age = timedelta(minutes=15)
            cls._instance._db_session_factory: Callable | None = None
        return cls._instance

    def set_db_session_factory(self, factory: Callable) -> None:
        """Set database session factory for event persistence."""
        self._db_session_factory = factory

    # === SUBSCRIPTION ===

    def subscribe(
        self,
        event_type: str | EventType,
        handler: Callable[[Event], Any],
    ) -> None:
        """Subscribe a handler to an event type."""
        key = event_type.value if isinstance(event_type, EventType) else event_type
        self._subscribers[key].append(handler)
        logger.debug(f"Subscribed handler to {key}")

    def unsubscribe(
        self,
        event_type: str | EventType,
        handler: Callable,
    ) -> None:
        """Unsubscribe a handler from an event type."""
        key = event_type.value if isinstance(event_type, EventType) else event_type
        if handler in self._subscribers[key]:
            self._subscribers[key].remove(handler)

    def subscribe_all(self, handler: Callable[[Event], Any]) -> None:
        """Subscribe to all events (wildcard)."""
        self._subscribers["*"].append(handler)

    # === EMISSION ===

    async def emit(
        self,
        event_type: str | EventType,
        source: str,
        payload: dict[str, Any],
        user_id: UUID | None = None,
        severity: EventSeverity = EventSeverity.INFO,
        persist: bool = True,
    ) -> Event:
        """
        Emit an event:
        1. Create Event object
        2. Call all subscribers
        3. Add to SSE buffer
        4. Optionally persist to database
        5. Push to all SSE clients
        """
        type_str = event_type.value if isinstance(event_type, EventType) else event_type

        event = Event(
            type=type_str,
            source=source,
            payload=payload,
            user_id=user_id,
            severity=severity,
        )

        # 1. Notify subscribers (async)
        handlers = self._subscribers.get(type_str, []) + self._subscribers.get("*", [])

        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Handler error for {type_str}: {e}")

        # 2. Add to buffer
        self._add_to_buffer(event)

        # 3. Persist if needed
        if persist and self._db_session_factory:
            await self._persist_event(event)

        # 4. Push to SSE clients
        await self._push_to_sse_clients(event)

        logger.debug(f"Emitted event: {type_str} from {source}")
        return event

    def emit_sync(
        self,
        event_type: str | EventType,
        source: str,
        payload: dict[str, Any],
        **kwargs: Any,
    ) -> None:
        """
        Synchronous emit for Celery context.
        Uses Redis pub/sub to communicate with main process.
        """
        import redis
        from app.config import settings

        type_str = event_type.value if isinstance(event_type, EventType) else event_type

        event_data = {
            "type": type_str,
            "source": source,
            "payload": payload,
            "timestamp": datetime.utcnow().isoformat(),
            **kwargs,
        }

        r = redis.from_url(settings.redis_url)
        r.publish("events", json.dumps(event_data, default=str))

    # === BUFFER MANAGEMENT ===

    def _add_to_buffer(self, event: Event) -> None:
        """Add event to ring buffer."""
        self._event_buffer.append(event)

        # Trim by size
        if len(self._event_buffer) > self._buffer_max_size:
            self._event_buffer = self._event_buffer[-self._buffer_max_size:]

        # Trim by age
        cutoff = datetime.utcnow() - self._buffer_max_age
        self._event_buffer = [e for e in self._event_buffer if e.timestamp > cutoff]

    def get_recent_events(
        self,
        minutes: int = 5,
        event_types: list[str] | None = None,
        source_filter: str | None = None,
    ) -> list[Event]:
        """Get recent events from buffer."""
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)

        events = [e for e in self._event_buffer if e.timestamp > cutoff]

        if event_types:
            events = [e for e in events if e.type in event_types]

        if source_filter:
            events = [e for e in events if source_filter in e.source]

        return sorted(events, key=lambda e: e.timestamp, reverse=True)

    # === SSE MANAGEMENT ===

    def register_sse_client(self, client_queue: asyncio.Queue) -> None:
        """Register a new SSE client."""
        self._sse_clients.add(client_queue)

    def unregister_sse_client(self, client_queue: asyncio.Queue) -> None:
        """Unregister an SSE client."""
        self._sse_clients.discard(client_queue)

    async def _push_to_sse_clients(self, event: Event) -> None:
        """Push event to all SSE clients."""
        dead_clients: set[asyncio.Queue] = set()

        for client_queue in self._sse_clients:
            try:
                client_queue.put_nowait(event)
            except asyncio.QueueFull:
                dead_clients.add(client_queue)

        # Cleanup dead clients
        for dead in dead_clients:
            self._sse_clients.discard(dead)

    # === PERSISTENCE ===

    async def _persist_event(self, event: Event) -> None:
        """Persist event to database."""
        if not self._db_session_factory:
            return

        try:
            async with self._db_session_factory() as session:
                db_event = SystemEvent(
                    id=event.id,
                    event_type=event.type,
                    source=event.source,
                    severity=event.severity.value,
                    payload=event.payload,
                    user_id=event.user_id,
                )
                session.add(db_event)
                await session.commit()
        except Exception as e:
            logger.error(f"Failed to persist event: {e}")


def get_event_bus() -> EventBus:
    """Get the singleton EventBus instance."""
    return EventBus()
