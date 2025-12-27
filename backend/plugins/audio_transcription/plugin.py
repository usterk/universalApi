"""Audio Transcription plugin implementation.

Universal Document Pattern: Output is a child Document with transcription in properties.
This is the basic transcription plugin (without word-level timestamps).
For word timestamps, use audio_transcription_words plugin.
"""

from typing import Any, Sequence

from fastapi import APIRouter
from sqlalchemy.orm import DeclarativeBase

from app.core.plugins.base import BasePlugin, PluginMetadata, PluginCapabilities


class AudioTranscriptionPlugin(BasePlugin):
    """
    Plugin for transcribing audio files using OpenAI.

    Features:
    - Full text transcription
    - Language detection
    - High accuracy transcription

    Universal Document Pattern: Output is a child Document with transcription in properties.
    This plugin creates basic transcription WITHOUT word-level timestamps.
    For word timestamps, use audio_transcription_words plugin.
    """

    SUPPORTED_TYPES = ["audio"]

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="audio_transcription",
            version="2.0.0",  # Major version bump for Universal Document Pattern
            display_name="Audio Transcription",
            description="Transcribe audio files using OpenAI (basic, without word timestamps)",
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
                    "model": {
                        "type": "string",
                        "enum": ["gpt-4o-mini-transcribe", "gpt-4o-transcribe", "whisper-1"],
                        "default": "gpt-4o-mini-transcribe",
                        "title": "Model",
                        "description": "OpenAI transcription model to use",
                    },
                    "language": {
                        "type": "string",
                        "default": "",
                        "title": "Language",
                        "description": "ISO 639-1 code (e.g., 'en', 'pl'). Empty = auto-detect",
                    },
                },
            },
        )

    @property
    def capabilities(self) -> PluginCapabilities:
        return PluginCapabilities(
            has_routes=False,  # No dedicated routes - use /documents API
            has_models=False,  # No dedicated models - uses Document
            has_tasks=True,
            has_event_handlers=True,
            has_frontend=False,  # No dedicated frontend - uses document detail view
            has_document_types=True,
        )

    async def setup(self, settings: dict[str, Any]) -> None:
        """Initialize plugin."""
        self._settings = settings
        self._model = settings.get("model", "gpt-4o-mini-transcribe")
        self._language = settings.get("language", "")

    def get_router(self) -> APIRouter | None:
        """No dedicated router - uses /documents API."""
        return None

    def get_models(self) -> Sequence[type[DeclarativeBase]]:
        """No dedicated models - uses Document."""
        return []

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
                "metadata_schema": {
                    "type": "object",
                    "required": ["full_text"],
                    "properties": {
                        "full_text": {"type": "string"},
                        "language": {"type": "string"},
                        "duration_seconds": {"type": "number"},
                        "model_used": {"type": "string"},
                    },
                },
            },
        ]
