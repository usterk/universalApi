"""Audio Transcription plugin."""

from plugins.audio_transcription.plugin import AudioTranscriptionPlugin

# Import tasks to register them with Celery
from plugins.audio_transcription import tasks  # noqa: F401

__all__ = ["AudioTranscriptionPlugin"]
