"""Audio Transcription with Speaker Diarization plugin."""

from plugins.audio_transcription_diarize.plugin import AudioTranscriptionDiarizePlugin

# Import tasks to register them with Celery
from plugins.audio_transcription_diarize import tasks  # noqa: F401

__all__ = ["AudioTranscriptionDiarizePlugin"]
