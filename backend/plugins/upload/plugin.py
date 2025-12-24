"""Upload plugin implementation."""

from typing import Any

from fastapi import APIRouter

from app.core.plugins.base import BasePlugin, PluginMetadata, PluginCapabilities


class UploadPlugin(BasePlugin):
    """
    Core plugin for file upload and storage.

    Handles:
    - File uploads via API
    - Storage management (local, S3)
    - Document creation
    """

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="upload",
            version="1.0.0",
            display_name="File Upload",
            description="Core file upload and storage plugin",
            author="UniversalAPI",
            input_types=[],  # Doesn't process documents
            output_type=None,
            priority=10,  # Highest priority - runs first
            dependencies=[],
            max_concurrent_jobs=10,
            color="#F59E0B",  # Amber 500
            required_env_vars=[],
            settings_schema={
                "type": "object",
                "properties": {
                    "storage_type": {
                        "type": "string",
                        "enum": ["local", "s3"],
                        "default": "local",
                    },
                    "max_file_size_mb": {
                        "type": "integer",
                        "default": 100,
                    },
                },
            },
        )

    @property
    def capabilities(self) -> PluginCapabilities:
        return PluginCapabilities(
            has_routes=True,
            has_models=False,
            has_tasks=False,
            has_event_handlers=False,
            has_frontend=True,
            has_document_types=True,
        )

    async def setup(self, settings: dict[str, Any]) -> None:
        """Initialize plugin with settings."""
        self._settings = settings
        self._storage_type = settings.get("storage_type", "local")
        self._max_file_size = settings.get("max_file_size_mb", 100) * 1024 * 1024

    def get_router(self) -> APIRouter:
        """Return plugin router."""
        from plugins.upload.router import router
        return router

    def get_document_types(self) -> list[dict]:
        """Register document types for common file types."""
        return [
            {
                "name": "audio",
                "display_name": "Audio File",
                "mime_types": [
                    "audio/mpeg",
                    "audio/mp3",
                    "audio/wav",
                    "audio/ogg",
                    "audio/webm",
                    "audio/flac",
                    "audio/m4a",
                    "audio/x-m4a",
                ],
            },
            {
                "name": "video",
                "display_name": "Video File",
                "mime_types": [
                    "video/mp4",
                    "video/webm",
                    "video/ogg",
                    "video/quicktime",
                    "video/x-msvideo",
                ],
            },
            {
                "name": "image",
                "display_name": "Image File",
                "mime_types": [
                    "image/jpeg",
                    "image/png",
                    "image/gif",
                    "image/webp",
                    "image/svg+xml",
                ],
            },
            {
                "name": "code",
                "display_name": "Source Code",
                "mime_types": [
                    # Python
                    "text/x-python",
                    "text/x-script.python",
                    "application/x-python-code",
                    # JavaScript/TypeScript
                    "text/javascript",
                    "application/javascript",
                    "application/x-javascript",
                    "text/x-typescript",
                    "application/x-typescript",
                    # Java
                    "text/x-java-source",
                    "text/x-java",
                    # C/C++
                    "text/x-c",
                    "text/x-c++",
                    "text/x-c++src",
                    # Other common languages
                    "text/x-go",
                    "text/x-rust",
                    "text/x-ruby",
                    "text/x-php",
                    "text/x-csharp",
                    "text/x-swift",
                    "text/x-kotlin",
                ],
            },
            {
                "name": "markdown",
                "display_name": "Markdown Document",
                "mime_types": [
                    "text/markdown",
                    "text/x-markdown",
                ],
            },
            {
                "name": "text",
                "display_name": "Text File",
                "mime_types": [
                    "text/plain",
                    "text/html",
                    "text/css",
                    "text/csv",
                ],
            },
            {
                "name": "xml",
                "display_name": "XML Document",
                "mime_types": [
                    "application/xml",
                    "text/xml",
                ],
            },
            {
                "name": "yaml",
                "display_name": "YAML Document",
                "mime_types": [
                    "application/x-yaml",
                    "text/yaml",
                    "text/x-yaml",
                ],
            },
            {
                "name": "document",
                "display_name": "Document",
                "mime_types": [
                    "application/pdf",
                    "application/msword",
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                ],
            },
            {
                "name": "json",
                "display_name": "JSON Data",
                "mime_types": [
                    "application/json",
                ],
            },
        ]

    def get_frontend_manifest(self) -> dict:
        """Return frontend manifest."""
        return {
            "name": self.metadata.name,
            "displayName": self.metadata.display_name,
            "version": self.metadata.version,
            "color": self.metadata.color,
            "routes": [],
            "menuItems": [],
            "dashboardWidgets": [],
            "slots": {},
        }
