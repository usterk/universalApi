"""Plugin registry - central store for all loaded plugins."""

from typing import Callable

from fastapi import APIRouter
from sqlalchemy.orm import DeclarativeBase

from app.core.plugins.base import BasePlugin, PluginState


class PluginRegistry:
    """
    Central registry for plugins.
    Singleton - one instance per application.
    """

    _instance: "PluginRegistry | None" = None

    def __new__(cls) -> "PluginRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._plugins: dict[str, BasePlugin] = {}
            cls._instance._content_handlers: list[BasePlugin] = []
        return cls._instance

    @property
    def plugins(self) -> dict[str, BasePlugin]:
        """Get copy of plugins dict."""
        return self._plugins.copy()

    def register(self, plugin: BasePlugin) -> None:
        """Register a plugin."""
        name = plugin.metadata.name

        if name in self._plugins:
            raise ValueError(f"Plugin {name} already registered")

        self._plugins[name] = plugin

        # Register as content handler if it has input_types
        if plugin.metadata.input_types:
            self._content_handlers.append(plugin)

    def unregister(self, name: str) -> None:
        """Unregister a plugin."""
        if name in self._plugins:
            plugin = self._plugins.pop(name)
            if plugin in self._content_handlers:
                self._content_handlers.remove(plugin)

    def get(self, name: str) -> BasePlugin | None:
        """Get plugin by name."""
        return self._plugins.get(name)

    def get_active_plugins(self) -> list[BasePlugin]:
        """Get only active plugins."""
        return [p for p in self._plugins.values() if p.state == PluginState.ACTIVE]

    def get_plugins_by_priority(self) -> list[BasePlugin]:
        """Get active plugins sorted by priority (lower first)."""
        return sorted(
            self.get_active_plugins(),
            key=lambda p: p.metadata.priority,
        )

    def collect_routers(self) -> list[tuple[str, APIRouter]]:
        """Collect routers from all plugins."""
        routers = []
        for plugin in self.get_active_plugins():
            if plugin.capabilities.has_routes:
                router = plugin.get_router()
                if router:
                    routers.append((plugin.name, router))
        return routers

    def collect_models(self) -> list[type[DeclarativeBase]]:
        """Collect DB models from all plugins."""
        models = []
        for plugin in self.get_active_plugins():
            if plugin.capabilities.has_models:
                models.extend(plugin.get_models())
        return models

    def collect_tasks(self) -> dict[str, Callable]:
        """Collect Celery tasks from all plugins."""
        tasks = {}
        for plugin in self.get_active_plugins():
            if plugin.capabilities.has_tasks:
                plugin_tasks = plugin.get_tasks()
                # Prefix task names with plugin name
                for task_name, task_func in plugin_tasks.items():
                    full_name = f"{plugin.name}.{task_name}"
                    tasks[full_name] = task_func
        return tasks

    def collect_document_types(self) -> list[dict]:
        """Collect document types from all plugins."""
        doc_types = []
        for plugin in self.get_active_plugins():
            if plugin.capabilities.has_document_types:
                types = plugin.get_document_types()
                for dt in types:
                    dt["registered_by"] = plugin.name
                    doc_types.append(dt)
        return doc_types

    def get_handlers_for_document_type(self, doc_type: str) -> list[BasePlugin]:
        """
        Get plugins that can handle a specific document type.
        Returns plugins sorted by priority.
        """
        handlers = [
            p
            for p in self._content_handlers
            if doc_type in p.metadata.input_types and p.state == PluginState.ACTIVE
        ]
        return sorted(handlers, key=lambda p: p.metadata.priority)

    def get_frontend_manifests(self) -> dict[str, dict]:
        """Collect frontend manifests from plugins."""
        manifests = {}
        for plugin in self.get_active_plugins():
            if plugin.capabilities.has_frontend:
                manifest = plugin.get_frontend_manifest()
                if manifest:
                    manifests[plugin.name] = manifest
        return manifests
