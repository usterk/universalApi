"""Plugin system module."""

from app.core.plugins.base import BasePlugin, PluginMetadata, PluginCapabilities, PluginState
from app.core.plugins.registry import PluginRegistry
from app.core.plugins.loader import PluginLoader
from app.core.plugins.models import PluginConfig, PluginFilter, ProcessingJob, JobStatus

__all__ = [
    "BasePlugin",
    "PluginMetadata",
    "PluginCapabilities",
    "PluginState",
    "PluginRegistry",
    "PluginLoader",
    "PluginConfig",
    "PluginFilter",
    "ProcessingJob",
    "JobStatus",
]
