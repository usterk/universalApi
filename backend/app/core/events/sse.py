"""SSE (Server-Sent Events) endpoint for real-time event streaming."""

import asyncio
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, Query
from sse_starlette.sse import EventSourceResponse

from app.core.events.bus import EventBus, get_event_bus
from app.core.events.types import Event
from app.core.auth.dependencies import CurrentUserFromQueryToken

router = APIRouter()


async def event_generator(
    event_bus: EventBus,
    event_types: list[str] | None = None,
    minutes: int = 5,
) -> AsyncGenerator[dict, None]:
    """
    Generator for SSE events.

    SSE format:
    event: <event_type>
    data: <json_payload>
    id: <event_id>
    """
    queue: asyncio.Queue[Event] = asyncio.Queue(maxsize=100)

    # Register client
    event_bus.register_sse_client(queue)

    try:
        # 1. Send initial batch (recent events)
        recent = event_bus.get_recent_events(minutes=minutes, event_types=event_types)

        for event in recent:
            yield format_sse_event(event)

        # 2. Stream new events
        while True:
            try:
                # 15 second keepalive interval for faster detection of connection issues
                event = await asyncio.wait_for(queue.get(), timeout=15)

                # Filter if needed
                if event_types and event.type not in event_types:
                    continue

                yield format_sse_event(event)

            except asyncio.TimeoutError:
                # Send keepalive every 15 seconds
                yield {"event": "keepalive", "data": ""}

    finally:
        event_bus.unregister_sse_client(queue)


def format_sse_event(event: Event) -> dict:
    """Format event for SSE."""
    import json

    # Create event data structure expected by frontend
    event_data = {
        "id": str(event.id),
        "type": event.type,
        "data": event.payload,  # Send only payload as data
        "timestamp": event.timestamp.isoformat(),
    }

    return {
        "event": event.type,
        "data": json.dumps(event_data),
        "id": str(event.id),
        "retry": 5000,
    }


@router.get("/stream")
async def stream_events(
    user: CurrentUserFromQueryToken,
    event_bus: EventBus = Depends(get_event_bus),
    types: str | None = Query(None, description="Comma-separated event types"),
    minutes: int = Query(5, ge=1, le=60, description="Initial history in minutes"),
) -> EventSourceResponse:
    """
    SSE endpoint for timeline events.

    Parameters:
    - token: JWT access token (required for authentication)
    - types: Filter by event types (e.g., "job.progress,job.completed")
    - minutes: How many minutes of history to send initially (1-60)

    Returns:
    - SSE stream with events

    Note: EventSource API doesn't support custom headers, so token must be passed as query parameter.
    """
    event_types = types.split(",") if types else None

    return EventSourceResponse(
        event_generator(event_bus, event_types, minutes),
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
        },
    )


@router.get("/recent")
async def get_recent_events(
    user: CurrentUserFromQueryToken,
    event_bus: EventBus = Depends(get_event_bus),
    minutes: int = Query(5, ge=1, le=60),
    types: str | None = Query(None),
    source: str | None = Query(None),
) -> dict:
    """REST endpoint for recent events history."""
    event_types = types.split(",") if types else None

    events = event_bus.get_recent_events(
        minutes=minutes,
        event_types=event_types,
        source_filter=source,
    )

    return {
        "events": [e.model_dump() for e in events],
        "count": len(events),
    }
