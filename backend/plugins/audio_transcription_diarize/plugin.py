"""Audio Transcription with Speaker Diarization plugin implementation."""

from typing import Any, Sequence

from fastapi import APIRouter
from sqlalchemy.orm import DeclarativeBase

from app.core.plugins.base import BasePlugin, PluginMetadata, PluginCapabilities


class AudioTranscriptionDiarizePlugin(BasePlugin):
    """
    Plugin for transcribing audio files with speaker diarization.

    Features:
    - Full text transcription
    - Speaker identification (who said what)
    - Segment-level timestamps per speaker
    - Language detection

    Universal Document Pattern: Output is a child Document with speakers[] in properties.
    """

    SUPPORTED_TYPES = ["audio"]

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="audio_transcription_diarize",
            version="1.0.0",
            display_name="Audio Transcription (Speaker ID)",
            description="Transcribe audio with speaker identification using OpenAI",
            author="UniversalAPI",
            input_types=self.SUPPORTED_TYPES,
            output_type="transcription_diarize",
            priority=22,  # After word transcription (21)
            dependencies=["upload"],
            max_concurrent_jobs=3,
            color="#EC4899",  # Pink
            required_env_vars=["OPENAI_API_KEY"],
            settings_schema={
                "type": "object",
                "properties": {
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
        self._language = settings.get("language", "")

    def get_router(self) -> APIRouter | None:
        """No dedicated router - uses /documents API."""
        return None

    def get_models(self) -> Sequence[type[DeclarativeBase]]:
        """No dedicated models - uses Document."""
        return []

    def get_tasks(self) -> dict:
        """Return Celery tasks."""
        from plugins.audio_transcription_diarize.tasks import transcribe_audio_diarize
        return {
            "process": transcribe_audio_diarize,
        }

    def get_event_handlers(self) -> dict:
        """Return event handlers."""
        from plugins.audio_transcription_diarize.handlers import on_document_created
        return {
            "document.created": [on_document_created],
        }

    def get_document_types(self) -> list[dict]:
        """Register transcription_diarize document type."""
        return [
            {
                "name": "transcription_diarize",
                "display_name": "Transcription with Speaker ID",
                "mime_types": ["application/json"],
                "metadata_schema": {
                    "type": "object",
                    "required": ["full_text", "segments"],
                    "properties": {
                        "full_text": {"type": "string"},
                        "language": {"type": "string"},
                        "duration_seconds": {"type": "number"},
                        "model_used": {"type": "string"},
                        "speaker_count": {"type": "integer"},
                        "segment_count": {"type": "integer"},
                        "segments": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "speaker": {"type": "string"},
                                    "text": {"type": "string"},
                                    "start": {"type": "number"},
                                    "end": {"type": "number"},
                                },
                            },
                        },
                    },
                },
            },
        ]
