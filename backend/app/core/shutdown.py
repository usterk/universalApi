"""Graceful shutdown coordinator.

This module handles graceful shutdown of the application with:
- Signal handlers for SIGTERM and SIGINT
- 30-second timeout (Kubernetes-compatible)
- Callback system for cleanup tasks
- Shutdown state tracking
"""

import asyncio
import signal
from datetime import datetime
from typing import Callable

from app.core.logging import get_logger

logger = get_logger(__name__)


class ShutdownCoordinator:
    """
    Coordinates graceful shutdown across all application components.

    Responsibilities:
    - Register signal handlers (SIGTERM, SIGINT)
    - Track shutdown state
    - Wait for running tasks with timeout
    - Emit shutdown events
    - Block new tasks during shutdown

    Usage:
        coordinator = get_shutdown_coordinator()
        coordinator.setup_signal_handlers()
        coordinator.register_callback(my_cleanup_func)

        # Check if shutting down
        if coordinator.is_shutdown_requested():
            # Block new operations
            pass
    """

    def __init__(self, timeout: int = 30):
        """
        Initialize shutdown coordinator.

        Args:
            timeout: Maximum seconds to wait for graceful shutdown (default: 30)
        """
        self.timeout = timeout
        self.shutdown_event = asyncio.Event()
        self.is_shutting_down = False
        self._shutdown_callbacks: list[Callable] = []
        logger.info("shutdown_coordinator_initialized", timeout_seconds=timeout)

    def register_callback(self, callback: Callable) -> None:
        """Register a callback to run during shutdown.

        Args:
            callback: Function to call during shutdown (can be sync or async)
        """
        self._shutdown_callbacks.append(callback)
        logger.debug("shutdown_callback_registered", callback_name=callback.__name__)

    def is_shutdown_requested(self) -> bool:
        """Check if shutdown has been requested.

        Returns:
            True if shutdown is in progress, False otherwise
        """
        return self.is_shutting_down

    def setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown.

        Registers handlers for:
        - SIGTERM (kill command, Kubernetes shutdown)
        - SIGINT (Ctrl+C)
        """

        def signal_handler(signum: int, frame) -> None:
            """Handle shutdown signals.

            Args:
                signum: Signal number
                frame: Current stack frame
            """
            sig_name = signal.Signals(signum).name
            logger.warning(
                "shutdown_signal_received",
                signal=sig_name,
                timeout_seconds=self.timeout,
            )

            # Set shutdown flag immediately
            self.is_shutting_down = True

            # Trigger async shutdown
            try:
                asyncio.create_task(self._initiate_shutdown())
            except RuntimeError:
                # No event loop running - shutdown will be handled by lifespan
                logger.debug("shutdown_no_event_loop", signal=sig_name)

        # Register handlers
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

        logger.info("shutdown_handlers_registered", signals=["SIGTERM", "SIGINT"])

    async def _initiate_shutdown(self) -> None:
        """Initiate graceful shutdown sequence.

        Runs all registered callbacks and signals the shutdown event.
        """
        logger.info("shutdown_initiated", timeout_seconds=self.timeout)

        # Run shutdown callbacks
        for callback in self._shutdown_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback()
                else:
                    callback()
            except Exception as e:
                logger.error(
                    "shutdown_callback_error",
                    callback_name=callback.__name__,
                    error=str(e),
                )

        # Signal shutdown event
        self.shutdown_event.set()

    async def wait_for_shutdown(self) -> None:
        """Wait for shutdown signal.

        This is a blocking coroutine that waits until shutdown is requested.
        """
        await self.shutdown_event.wait()

    async def shutdown_with_timeout(self, coro) -> None:
        """Execute shutdown coroutine with timeout.

        Args:
            coro: Coroutine to execute

        Logs warning if timeout is exceeded.
        """
        try:
            await asyncio.wait_for(coro, timeout=self.timeout)
            logger.info("shutdown_completed_gracefully")
        except asyncio.TimeoutError:
            logger.warning(
                "shutdown_timeout_exceeded",
                timeout_seconds=self.timeout,
                message="Some tasks may not have completed",
            )


# Global singleton
_coordinator: ShutdownCoordinator | None = None


def get_shutdown_coordinator() -> ShutdownCoordinator:
    """Get the global shutdown coordinator.

    Returns:
        Singleton instance of ShutdownCoordinator
    """
    global _coordinator
    if _coordinator is None:
        from app.config import settings

        timeout = getattr(settings, "shutdown_timeout_seconds", 30)
        _coordinator = ShutdownCoordinator(timeout=timeout)
    return _coordinator
