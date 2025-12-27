"""OpenAI AI provider."""

import io
from typing import Any

from openai import AsyncOpenAI

from app.config import settings
from app.core.ai.base import (
    AIProvider,
    DiarizeResult,
    DiarizeSegment,
    TranscriptionResult,
    TranscriptionWord,
)


class OpenAIProvider(AIProvider):
    """
    OpenAI provider for transcription using gpt-4o-mini-transcribe.

    Features:
    - High quality transcription
    - Word-level timestamps
    - Language detection
    - Streaming support (future)
    """

    # whisper-1 is the only model supporting verbose_json with word timestamps ($0.006/min)
    # gpt-4o-transcribe/gpt-4o-mini-transcribe are newer but don't support word timestamps
    TRANSCRIPTION_MODEL = "whisper-1"  # Only model supporting verbose_json + word timestamps
    DIARIZATION_MODEL = "gpt-4o-transcribe-diarize"
    COMPLETION_MODEL = "gpt-4o-mini"

    def __init__(self, api_key: str | None = None):
        self._client = AsyncOpenAI(api_key=api_key or settings.openai_api_key)

    @property
    def name(self) -> str:
        return "openai"

    async def transcribe(
        self,
        audio_data: bytes,
        language: str | None = None,
        filename: str = "audio.mp3",
        **kwargs: Any,
    ) -> TranscriptionResult:
        """
        Transcribe audio using gpt-4o-mini-transcribe.

        Args:
            audio_data: Raw audio bytes
            language: Optional language code (e.g., "en", "pl")
            filename: Filename with extension for format detection

        Returns:
            TranscriptionResult with text and word timestamps
        """
        # Create file-like object
        audio_file = io.BytesIO(audio_data)
        audio_file.name = filename

        # Call OpenAI API with verbose_json for word-level timestamps
        transcription_params: dict[str, Any] = {
            "model": self.TRANSCRIPTION_MODEL,
            "file": audio_file,
            "response_format": "verbose_json",
            "timestamp_granularities": ["word"],
        }

        if language:
            transcription_params["language"] = language

        response = await self._client.audio.transcriptions.create(**transcription_params)

        # Parse words with timestamps from verbose_json response
        words = []
        if hasattr(response, "words") and response.words:
            for w in response.words:
                words.append(
                    TranscriptionWord(
                        word=w.word,
                        start=w.start,
                        end=w.end,
                        confidence=getattr(w, "confidence", None),
                    )
                )

        return TranscriptionResult(
            text=response.text,
            language=getattr(response, "language", language or "unknown"),
            language_probability=getattr(response, "language_probability", None),
            duration=getattr(response, "duration", None),
            words=words,
            model=self.TRANSCRIPTION_MODEL,
            raw_response=response.model_dump() if hasattr(response, "model_dump") else {},
        )

    async def transcribe_diarize(
        self,
        audio_data: bytes,
        language: str | None = None,
        filename: str = "audio.mp3",
        **kwargs: Any,
    ) -> DiarizeResult:
        """
        Transcribe audio with speaker diarization using gpt-4o-transcribe-diarize.

        Args:
            audio_data: Raw audio bytes
            language: Optional language code (e.g., "en", "pl")
            filename: Filename with extension for format detection

        Returns:
            DiarizeResult with text and speaker segments
        """
        # Create file-like object
        audio_file = io.BytesIO(audio_data)
        audio_file.name = filename

        # Call OpenAI API with diarization model
        transcription_params: dict[str, Any] = {
            "model": self.DIARIZATION_MODEL,
            "file": audio_file,
            "response_format": "diarized_json",
        }

        if language:
            transcription_params["language"] = language

        response = await self._client.audio.transcriptions.create(**transcription_params)

        # Parse segments with speaker identification
        # Handle both object and dict response formats
        segments = []
        raw_segments = getattr(response, "segments", None) or []
        for seg in raw_segments:
            if isinstance(seg, dict):
                segments.append(
                    DiarizeSegment(
                        speaker=seg.get("speaker", "unknown"),
                        text=seg.get("text", ""),
                        start=seg.get("start", 0.0),
                        end=seg.get("end", 0.0),
                    )
                )
            else:
                segments.append(
                    DiarizeSegment(
                        speaker=getattr(seg, "speaker", "unknown"),
                        text=getattr(seg, "text", ""),
                        start=getattr(seg, "start", 0.0),
                        end=getattr(seg, "end", 0.0),
                    )
                )

        # Get text - handle both response formats
        text = getattr(response, "text", "") or ""
        if not text and segments:
            # Reconstruct from segments
            text = " ".join(seg.text for seg in segments)

        return DiarizeResult(
            text=text,
            language=getattr(response, "language", language or "unknown"),
            duration=getattr(response, "duration", None),
            segments=segments,
            model=self.DIARIZATION_MODEL,
            raw_response=response.model_dump() if hasattr(response, "model_dump") else {},
        )

    async def complete(
        self,
        prompt: str,
        system: str | None = None,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> str:
        """
        Text completion using GPT-4o-mini.

        Args:
            prompt: User prompt
            system: Optional system message
            max_tokens: Maximum response tokens
            temperature: Sampling temperature

        Returns:
            Generated text
        """
        messages = []

        if system:
            messages.append({"role": "system", "content": system})

        messages.append({"role": "user", "content": prompt})

        response = await self._client.chat.completions.create(
            model=self.COMPLETION_MODEL,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            **kwargs,
        )

        return response.choices[0].message.content or ""


# Singleton instance
_provider: OpenAIProvider | None = None


def get_openai_provider() -> OpenAIProvider:
    """Get singleton OpenAI provider."""
    global _provider
    if _provider is None:
        _provider = OpenAIProvider()
    return _provider
