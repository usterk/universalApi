"""OpenAI AI provider."""

import io
from typing import Any

from openai import AsyncOpenAI

from app.config import settings
from app.core.ai.base import AIProvider, TranscriptionResult, TranscriptionWord


class OpenAIProvider(AIProvider):
    """
    OpenAI provider for transcription using gpt-4o-mini-transcribe.

    Features:
    - High quality transcription
    - Word-level timestamps
    - Language detection
    - Streaming support (future)
    """

    TRANSCRIPTION_MODEL = "gpt-4o-mini-transcribe"
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

        # Call OpenAI API
        transcription_params = {
            "model": self.TRANSCRIPTION_MODEL,
            "file": audio_file,
            "response_format": "verbose_json",
            "timestamp_granularities": ["word"],
        }

        if language:
            transcription_params["language"] = language

        response = await self._client.audio.transcriptions.create(**transcription_params)

        # Parse words with timestamps
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
