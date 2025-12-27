"""Base AI provider interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class TranscriptionWord:
    """Word with timestamp."""

    word: str
    start: float  # seconds
    end: float  # seconds
    confidence: float | None = None


@dataclass
class TranscriptionResult:
    """Result of audio transcription."""

    text: str
    language: str
    language_probability: float | None = None
    duration: float | None = None  # seconds
    words: list[TranscriptionWord] = field(default_factory=list)
    model: str = ""
    raw_response: dict = field(default_factory=dict)


@dataclass
class DiarizeSegment:
    """Segment with speaker identification."""

    speaker: str
    text: str
    start: float  # seconds
    end: float  # seconds


@dataclass
class DiarizeResult:
    """Result of audio transcription with speaker diarization."""

    text: str
    language: str
    duration: float | None = None  # seconds
    segments: list[DiarizeSegment] = field(default_factory=list)
    model: str = ""
    raw_response: dict = field(default_factory=dict)


class AIProvider(ABC):
    """Abstract base class for AI providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name."""
        ...

    @abstractmethod
    async def transcribe(
        self,
        audio_data: bytes,
        language: str | None = None,
        **kwargs: Any,
    ) -> TranscriptionResult:
        """Transcribe audio data."""
        ...

    async def transcribe_diarize(
        self,
        audio_data: bytes,
        language: str | None = None,
        **kwargs: Any,
    ) -> DiarizeResult:
        """Transcribe audio with speaker diarization (optional)."""
        raise NotImplementedError("Speaker diarization not supported by this provider")

    async def complete(
        self,
        prompt: str,
        system: str | None = None,
        **kwargs: Any,
    ) -> str:
        """Text completion (optional)."""
        raise NotImplementedError("Text completion not supported by this provider")
