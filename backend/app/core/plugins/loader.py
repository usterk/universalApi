"""Plugin loader - autodiscovery and loading of plugins."""

import importlib
import importlib.util
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from app.core.plugins.base import BasePlugin, PluginState, PluginMetadata
from app.core.plugins.registry import PluginRegistry

if TYPE_CHECKING:
    from app.core.events.bus import EventBus

logger = logging.getLogger(__name__)


class PluginLoadError(Exception):
    """Error loading a plugin."""

    pass


class PluginDependencyError(Exception):
    """Error resolving plugin dependencies."""

    pass


class PluginLoader:
    """
    Responsible for:
    1. Autodiscovery of plugins in plugins/ directory
    2. Validation of plugin structure
    3. Loading in correct order (respecting dependencies)
    4. Registration in PluginRegistry
    """

    PLUGINS_DIR = Path(__file__).parent.parent.parent.parent / "plugins"
    REQUIRED_FILES = ["__init__.py", "plugin.py"]

    def __init__(self, registry: PluginRegistry, event_bus: "EventBus") -> None:
        self.registry = registry
        self.event_bus = event_bus
        self._discovered: dict[str, Path] = {}

    def discover(self) -> list[str]:
        """
        Scan plugins/ directory and find all plugins.
        Returns list of discovered plugin names.
        """
        self._discovered.clear()

        if not self.PLUGINS_DIR.exists():
            logger.warning(f"Plugins directory not found: {self.PLUGINS_DIR}")
            return []

        for item in self.PLUGINS_DIR.iterdir():
            if not item.is_dir() or item.name.startswith("_"):
                continue

            # Check required files
            if self._validate_plugin_structure(item):
                self._discovered[item.name] = item
                logger.info(f"Discovered plugin: {item.name}")
            else:
                logger.warning(
                    f"Invalid plugin structure: {item.name} "
                    f"(missing required files)"
                )

        return list(self._discovered.keys())

    def _validate_plugin_structure(self, plugin_path: Path) -> bool:
        """Check if plugin has required structure."""
        for required in self.REQUIRED_FILES:
            if not (plugin_path / required).exists():
                return False
        return True

    async def load_all(self, settings: dict[str, dict]) -> dict[str, BasePlugin]:
        """
        Load all discovered plugins respecting dependencies.

        Args:
            settings: {plugin_name: {setting_key: value}}

        Returns:
            Map of name -> plugin instance
        """
        # 1. Load metadata from all plugins (without full initialization)
        metadata_map = self._load_all_metadata()

        # 2. Sort by dependencies (topological sort)
        load_order = self._resolve_load_order(metadata_map)

        # 3. Load in order
        loaded: dict[str, BasePlugin] = {}

        for plugin_name in load_order:
            try:
                plugin = await self._load_plugin(
                    plugin_name,
                    settings.get(plugin_name, {}),
                )
                loaded[plugin_name] = plugin
                self.registry.register(plugin)
                logger.info(f"Loaded plugin: {plugin_name}")

            except Exception as e:
                logger.error(f"Failed to load plugin {plugin_name}: {e}")
                # Continue with remaining plugins

        return loaded

    def _load_all_metadata(self) -> dict[str, PluginMetadata]:
        """Load only metadata without full initialization."""
        result = {}

        for name, path in self._discovered.items():
            try:
                # Import only plugin.py
                spec = importlib.util.spec_from_file_location(
                    f"plugins.{name}.plugin",
                    path / "plugin.py",
                )
                if spec is None or spec.loader is None:
                    continue

                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Find class inheriting from BasePlugin
                plugin_class = self._find_plugin_class(module)
                if plugin_class:
                    # Temporary instance just for metadata
                    temp_instance = plugin_class()
                    result[name] = temp_instance.metadata

            except Exception as e:
                logger.error(f"Failed to load metadata for {name}: {e}")

        return result

    def _find_plugin_class(self, module: object) -> type[BasePlugin] | None:
        """Find plugin class in module."""
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (
                isinstance(attr, type)
                and issubclass(attr, BasePlugin)
                and attr is not BasePlugin
            ):
                return attr
        return None

    def _resolve_load_order(self, metadata_map: dict[str, PluginMetadata]) -> list[str]:
        """
        Topological sort of plugins by dependencies.
        Raises PluginDependencyError on circular dependencies.
        """
        # Kahn's algorithm
        in_degree: dict[str, int] = {name: 0 for name in metadata_map}
        graph: dict[str, list[str]] = {name: [] for name in metadata_map}

        for name, meta in metadata_map.items():
            for dep in meta.dependencies:
                if dep not in metadata_map:
                    raise PluginDependencyError(
                        f"Plugin {name} depends on unknown plugin: {dep}"
                    )
                graph[dep].append(name)
                in_degree[name] += 1

        # Start with plugins with no dependencies
        queue = [name for name, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            current = queue.pop(0)
            result.append(current)

            for dependent in graph[current]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        if len(result) != len(metadata_map):
            raise PluginDependencyError("Circular dependency detected in plugins")

        return result

    async def _load_plugin(self, name: str, settings: dict) -> BasePlugin:
        """Full loading of a single plugin."""
        path = self._discovered[name]

        # Import module
        spec = importlib.util.spec_from_file_location(
            f"plugins.{name}.plugin",
            path / "plugin.py",
        )
        if spec is None or spec.loader is None:
            raise PluginLoadError(f"Cannot load spec for {name}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Find and create instance
        plugin_class = self._find_plugin_class(module)
        if not plugin_class:
            raise PluginLoadError(f"No plugin class found in {name}")

        plugin = plugin_class()
        plugin._state = PluginState.LOADING

        # Set event bus
        plugin.set_event_bus(self.event_bus)

        # Call setup
        try:
            await plugin.setup(settings)
            plugin._state = PluginState.ACTIVE
        except Exception as e:
            plugin._state = PluginState.ERROR
            raise PluginLoadError(f"Plugin {name} setup failed: {e}")

        # NOTE: Event handlers are registered in main.py after all plugins are loaded
        # to avoid duplicate registration

        return plugin
