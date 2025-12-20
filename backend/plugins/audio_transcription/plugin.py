"""Audio Transcription plugin implementation."""

from typing import Any, Sequence

from fastapi import APIRouter
from sqlalchemy.orm import DeclarativeBase

from app.core.plugins.base import BasePlugin, PluginMetadata, PluginCapabilities


class AudioTranscriptionPlugin(BasePlugin):
    """
    Plugin for transcribing audio files using OpenAI's gpt-4o-mini-transcribe.

    Features:
    - Word-level timestamps
    - Language detection
    - High accuracy transcription
    """

    SUPPORTED_TYPES = ["audio"]

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="audio_transcription",
            version="1.0.0",
            display_name="Audio Transcription",
            description="Transcribe audio files with word-level timestamps using OpenAI",
            author="UniversalAPI",
            input_types=self.SUPPORTED_TYPES,
            output_type="transcription",
            priority=20,  # After upload (10)
            dependencies=["upload"],
            max_concurrent_jobs=3,
            color="#3B82F6",  # Blue
            required_env_vars=["OPENAI_API_KEY"],
            settings_schema={
                "type": "object",
                "properties": {
                    "default_language": {
                        "type": "string",
                        "description": "Default language code (e.g., 'en', 'pl'). Leave empty for auto-detect.",
                        "default": "",
                    },
                    "model": {
                        "type": "string",
                        "enum": ["gpt-4o-mini-transcribe", "gpt-4o-transcribe", "whisper-1"],
                        "default": "gpt-4o-mini-transcribe",
                    },
                },
            },
        )

    @property
    def capabilities(self) -> PluginCapabilities:
        return PluginCapabilities(
            has_routes=True,
            has_models=True,
            has_tasks=True,
            has_event_handlers=True,
            has_frontend=True,
            has_document_types=True,
        )

    async def setup(self, settings: dict[str, Any]) -> None:
        """Initialize plugin."""
        self._settings = settings
        self._default_language = settings.get("default_language", "")
        self._model = settings.get("model", "gpt-4o-mini-transcribe")

    def get_router(self) -> APIRouter:
        """Return plugin router."""
        from plugins.audio_transcription.router import router
        return router

    def get_models(self) -> Sequence[type[DeclarativeBase]]:
        """Return plugin models."""
        from plugins.audio_transcription.models import Transcription, TranscriptionWord
        return [Transcription, TranscriptionWord]

    def get_tasks(self) -> dict:
        """Return Celery tasks."""
        from plugins.audio_transcription.tasks import transcribe_audio
        return {
            "process": transcribe_audio,
        }

    def get_event_handlers(self) -> dict:
        """Return event handlers."""
        from plugins.audio_transcription.handlers import on_document_created
        return {
            "document.created": [on_document_created],
        }

    def get_document_types(self) -> list[dict]:
        """Register transcription document type."""
        return [
            {
                "name": "transcription",
                "display_name": "Transcription",
                "mime_types": ["application/json"],
            },
        ]

    def get_frontend_manifest(self) -> dict:
        """Return frontend manifest."""
        return {
            "name": self.metadata.name,
            "displayName": self.metadata.display_name,
            "version": self.metadata.version,
            "color": self.metadata.color,
            "routes": [
                {"path": "/transcriptions", "componentName": "TranscriptionList"},
                {"path": "/transcriptions/:id", "componentName": "TranscriptionView"},
            ],
            "menuItems": [
                {
                    "label": "Transcriptions",
                    "path": "/transcriptions",
                    "icon": "FileAudio",
                    "order": 20,
                },
            ],
            "dashboardWidgets": [
                {
                    "id": "recent-transcriptions",
                    "title": "Recent Transcriptions",
                    "componentName": "RecentTranscriptionsWidget",
                    "position": "main",
                    "span": 2,
                    "order": 20,
                },
            ],
            "slots": {},
        }
