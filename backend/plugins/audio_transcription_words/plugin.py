"""Audio Transcription with Words plugin implementation."""

from typing import Any, Sequence

from fastapi import APIRouter
from sqlalchemy.orm import DeclarativeBase

from app.core.plugins.base import BasePlugin, PluginMetadata, PluginCapabilities


class AudioTranscriptionWordsPlugin(BasePlugin):
    """
    Plugin for transcribing audio files with word-level timestamps.

    Features:
    - Full text transcription
    - Word-level timestamps with start/end times
    - Word confidence scores
    - Language detection

    Universal Document Pattern: Output is a child Document with words[] in properties.
    """

    SUPPORTED_TYPES = ["audio"]

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="audio_transcription_words",
            version="1.0.0",
            display_name="Audio Transcription (with Words)",
            description="Transcribe audio with word-level timestamps using OpenAI",
            author="UniversalAPI",
            input_types=self.SUPPORTED_TYPES,
            output_type="transcription_words",
            priority=21,  # After basic transcription (20)
            dependencies=["upload"],
            max_concurrent_jobs=3,
            color="#8B5CF6",  # Purple (different from basic transcription)
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
        from plugins.audio_transcription_words.tasks import transcribe_audio_words
        return {
            "process": transcribe_audio_words,
        }

    def get_event_handlers(self) -> dict:
        """Return event handlers."""
        from plugins.audio_transcription_words.handlers import on_document_created
        return {
            "document.created": [on_document_created],
        }

    def get_document_types(self) -> list[dict]:
        """Register transcription_words document type."""
        return [
            {
                "name": "transcription_words",
                "display_name": "Transcription with Words",
                "mime_types": ["application/json"],
                "metadata_schema": {
                    "type": "object",
                    "required": ["full_text", "words"],
                    "properties": {
                        "full_text": {"type": "string"},
                        "language": {"type": "string"},
                        "duration_seconds": {"type": "number"},
                        "model_used": {"type": "string"},
                        "word_count": {"type": "integer"},
                        "words": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "word": {"type": "string"},
                                    "start": {"type": "number"},
                                    "end": {"type": "number"},
                                    "confidence": {"type": "number"},
                                },
                            },
                        },
                    },
                },
            },
        ]
