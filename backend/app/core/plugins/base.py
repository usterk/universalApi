"""Base plugin class and interfaces."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Sequence

from fastapi import APIRouter
from sqlalchemy.orm import DeclarativeBase

if TYPE_CHECKING:
    from app.core.events.bus import EventBus
    from app.core.documents.models import Document


class PluginState(str, Enum):
    """Plugin lifecycle states."""

    DISCOVERED = "discovered"
    LOADING = "loading"
    INSTALLED = "installed"
    ACTIVE = "active"
    DISABLED = "disabled"
    ERROR = "error"


@dataclass
class PluginMetadata:
    """Plugin metadata - defined in plugin.py."""

    name: str  # Unique slug, e.g., "audio-transcription"
    version: str  # Semver
    display_name: str
    description: str = ""
    author: str = ""

    # Processing config
    input_types: list[str] = field(default_factory=list)  # Document types this plugin handles
    output_type: str | None = None  # Document type this plugin produces
    priority: int = 100  # Lower = earlier (for deterministic ordering)
    dependencies: list[str] = field(default_factory=list)  # Other plugins required

    # Concurrency
    max_concurrent_jobs: int = 5

    # UI
    color: str = "#6366F1"  # Hex color for timeline

    # Configuration
    settings_schema: dict | None = None  # JSON Schema for plugin settings
    required_env_vars: list[str] = field(default_factory=list)


@dataclass
class PluginCapabilities:
    """Declaration of plugin capabilities."""

    has_routes: bool = False
    has_models: bool = False
    has_tasks: bool = False
    has_event_handlers: bool = False
    has_frontend: bool = False
    has_document_types: bool = False  # Can register new document types


class BasePlugin(ABC):
    """
    Abstract base class for all plugins.

    Each plugin MUST:
    1. Inherit from BasePlugin
    2. Implement metadata property
    3. Implement capabilities property
    4. Implement setup() method

    Plugin CAN:
    - Return router in get_router()
    - Return models in get_models()
    - Return tasks in get_tasks()
    - Register event handlers
    - Register new document types
    """

    def __init__(self) -> None:
        self._state = PluginState.DISCOVERED
        self._settings: dict[str, Any] = {}
        self._event_bus: "EventBus | None" = None

    # === ABSTRACT (required) ===

    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        ...

    @property
    @abstractmethod
    def capabilities(self) -> PluginCapabilities:
        """Declare plugin capabilities."""
        ...

    @abstractmethod
    async def setup(self, settings: dict[str, Any]) -> None:
        """
        Initialize plugin with settings.
        Called at application startup.
        """
        ...

    # === OPTIONAL (override as needed) ===

    async def install(self) -> None:
        """
        Called on first installation.
        Use for one-time setup like running migrations.
        """
        pass

    async def uninstall(self) -> None:
        """
        Called when plugin is being removed.
        Use for cleanup.
        """
        pass

    def get_router(self) -> APIRouter | None:
        """Return FastAPI router with plugin endpoints."""
        return None

    def get_models(self) -> Sequence[type[DeclarativeBase]]:
        """Return SQLAlchemy models to register."""
        return []

    def get_tasks(self) -> dict[str, Callable]:
        """Return map of task_name -> function for Celery."""
        return {}

    def get_event_handlers(self) -> dict[str, list[Callable]]:
        """
        Return map of event_type -> [handlers].
        Handler: async def handler(event: Event) -> None
        """
        return {}

    def get_document_types(self) -> list[dict]:
        """
        Return document types to register.
        Each: {"name": "...", "display_name": "...", "mime_types": [...]}
        """
        return []

    def get_frontend_manifest(self) -> dict | None:
        """Return frontend manifest for UI extensions."""
        return None

    async def should_process(self, document: "Document") -> bool:
        """
        Check if this plugin should process the given document.
        Override for custom filtering logic beyond input_types.
        """
        # Default: check if document type matches input_types
        doc_type = document.document_type.name if document.document_type else None
        return doc_type in self.metadata.input_types

    async def process(self, document: "Document") -> dict[str, Any]:
        """
        Process a document.
        Override this for the main processing logic.
        Returns result dict.
        """
        raise NotImplementedError("Plugin must implement process() method")

    async def on_startup(self) -> None:
        """Hook called after full initialization."""
        pass

    async def on_shutdown(self) -> None:
        """Hook called at application shutdown."""
        pass

    async def healthcheck(self) -> dict[str, Any]:
        """Check plugin health status."""
        return {"status": "healthy"}

    # === UTILITY (don't override) ===

    @property
    def state(self) -> PluginState:
        return self._state

    @property
    def name(self) -> str:
        return self.metadata.name

    @property
    def settings(self) -> dict[str, Any]:
        return self._settings

    def set_event_bus(self, bus: "EventBus") -> None:
        """Set by loader - gives access to event bus."""
        self._event_bus = bus

    async def emit_event(self, event_type: str, payload: dict) -> None:
        """Helper to emit events."""
        if self._event_bus:
            await self._event_bus.emit(
                event_type=event_type,
                source=f"plugin:{self.name}",
                payload=payload,
            )
