"""Redis event subscriber for Celery-emitted events.

This module bridges the gap between Celery tasks (which use emit_sync via Redis pub/sub)
and the main EventBus (which pushes to SSE clients).

Without this subscriber, events emitted from Celery tasks never reach SSE clients!
"""

import asyncio
import json
from typing import TYPE_CHECKING

import redis.asyncio as redis

from app.config import settings
from app.core.logging import get_logger
from app.core.events.types import EventSeverity

if TYPE_CHECKING:
    from app.core.events.bus import EventBus

logger = get_logger(__name__)


class RedisEventSubscriber:
    """
    Subscribes to Redis "events" channel and relays to EventBus.

    This bridges Celery tasks (which use emit_sync via Redis pub/sub)
    with the main EventBus (which pushes to SSE clients).

    Usage:
        event_bus = get_event_bus()
        subscriber = RedisEventSubscriber(event_bus)
        task = asyncio.create_task(subscriber.start())
        # ... later ...
        subscriber.stop()
        await task
    """

    def __init__(self, event_bus: "EventBus"):
        """Initialize subscriber with EventBus reference.

        Args:
            event_bus: The EventBus instance to relay events to
        """
        self.event_bus = event_bus
        self.redis_client: redis.Redis | None = None
        self.pubsub: redis.client.PubSub | None = None
        self.running = False

    async def start(self) -> None:
        """Start listening to Redis events channel.

        This is a long-running coroutine that should be run as a background task.
        """
        self.running = True

        try:
            # Create Redis client
            self.redis_client = redis.from_url(settings.redis_url)
            self.pubsub = self.redis_client.pubsub()

            # Subscribe to events channel
            await self.pubsub.subscribe("events")
            logger.info("redis_subscriber_listening", channel="events")

            # Listen loop
            while self.running:
                try:
                    message = await self.pubsub.get_message(
                        ignore_subscribe_messages=True,
                        timeout=1.0,
                    )

                    if message and message["type"] == "message":
                        await self._handle_message(message["data"])

                except asyncio.CancelledError:
                    logger.info("redis_subscriber_cancelled")
                    break
                except Exception as e:
                    logger.error("redis_subscriber_error", error=str(e))
                    await asyncio.sleep(1)  # Brief pause before retry

        except Exception as e:
            logger.error("redis_subscriber_startup_error", error=str(e))
        finally:
            await self._cleanup()

    async def _handle_message(self, data: bytes) -> None:
        """Handle incoming Redis message.

        Args:
            data: Raw message data from Redis
        """
        try:
            event_data = json.loads(data.decode("utf-8"))

            # Extract fields
            event_type = event_data.get("type")
            source = event_data.get("source")
            payload = event_data.get("payload", {})
            severity_str = event_data.get("severity", "info")
            user_id = event_data.get("user_id")

            # Parse severity
            try:
                severity = EventSeverity(severity_str)
            except ValueError:
                severity = EventSeverity.INFO

            # Emit to EventBus (which will push to SSE clients)
            await self.event_bus.emit(
                event_type=event_type,
                source=source,
                payload=payload,
                severity=severity,
                user_id=user_id,
                persist=False,  # Don't persist - already handled by Celery task
            )

        except json.JSONDecodeError:
            logger.error("redis_subscriber_invalid_json", data=data[:100])
        except Exception as e:
            logger.error("redis_subscriber_handle_error", error=str(e))

    def stop(self) -> None:
        """Stop the subscriber.

        This sets the running flag to False, which will cause the listen loop to exit.
        """
        self.running = False
        logger.info("redis_subscriber_stopping")

    async def _cleanup(self) -> None:
        """Clean up Redis connections."""
        if self.pubsub:
            await self.pubsub.unsubscribe("events")
            await self.pubsub.close()

        if self.redis_client:
            await self.redis_client.close()

        logger.info("redis_subscriber_cleanup_complete")
