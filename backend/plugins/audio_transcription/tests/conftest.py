"""Plugin-specific fixtures for Audio Transcription plugin tests.

Import shared fixtures from main conftest.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

# Import all shared fixtures
from tests.conftest import *  # noqa: F401, F403


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for transcription tests."""
    client = MagicMock()

    # Mock transcription response
    transcription = MagicMock()
    transcription.text = "This is a test transcription."
    transcription.segments = []
    transcription.words = []

    client.audio.transcriptions.create = AsyncMock(return_value=transcription)

    return client


@pytest.fixture
def sample_transcription_result() -> dict:
    """Sample transcription result for testing."""
    return {
        "text": "This is a test transcription.",
        "language": "en",
        "duration": 5.0,
        "segments": [
            {
                "id": 0,
                "start": 0.0,
                "end": 2.5,
                "text": "This is a test",
            },
            {
                "id": 1,
                "start": 2.5,
                "end": 5.0,
                "text": " transcription.",
            },
        ],
        "words": [
            {"word": "This", "start": 0.0, "end": 0.5},
            {"word": "is", "start": 0.5, "end": 0.8},
            {"word": "a", "start": 0.8, "end": 1.0},
            {"word": "test", "start": 1.0, "end": 2.0},
            {"word": "transcription", "start": 2.5, "end": 4.5},
        ],
    }
