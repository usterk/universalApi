"""Audio Transcription with Words plugin."""

from plugins.audio_transcription_words.plugin import AudioTranscriptionWordsPlugin

# Import tasks to register them with Celery
from plugins.audio_transcription_words import tasks  # noqa: F401

__all__ = ["AudioTranscriptionWordsPlugin"]
