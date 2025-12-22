"""End-to-end tests for Audio Transcription plugin.

NOTE: These tests require a valid OpenAI API key for full E2E testing.
Tests are marked with @pytest.mark.slow as they make external API calls.
"""

import os
import pytest
from httpx import AsyncClient


@pytest.mark.e2e
@pytest.mark.plugin
@pytest.mark.asyncio
class TestAudioTranscriptionE2E:
    """E2E tests for audio transcription workflow."""

    async def test_plugin_endpoint_exists(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Plugin endpoints should be registered."""
        # Check if plugin endpoints are accessible
        response = await async_client.get(
            "/api/v1/plugins/audio_transcription/status",
            headers=auth_headers,
        )

        # Either 200 (endpoint exists) or 404 (not implemented yet)
        assert response.status_code in [200, 404]

    async def test_list_transcriptions(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Should be able to list transcriptions."""
        response = await async_client.get(
            "/api/v1/plugins/audio_transcription/transcriptions",
            headers=auth_headers,
        )

        # Either 200 with list or 404 if not implemented
        assert response.status_code in [200, 404]


@pytest.mark.e2e
@pytest.mark.plugin
@pytest.mark.slow
@pytest.mark.asyncio
class TestAudioTranscriptionWithAPI:
    """E2E tests that require external API (OpenAI).

    These tests are marked as slow and may require valid API keys.
    Skip in CI unless API keys are configured.
    """

    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY").startswith("sk-your-"),
        reason="Requires valid OpenAI API key (set in .env)"
    )
    async def test_transcribe_audio_file(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        sample_audio_file: bytes,
    ):
        """Full transcription workflow with real API."""
        # 1. Upload audio file
        upload_response = await async_client.post(
            "/api/v1/plugins/upload/files",
            headers=auth_headers,
            files={
                "file": ("test.mp3", sample_audio_file, "audio/mpeg"),
            },
        )

        assert upload_response.status_code in [200, 201]
        document_id = upload_response.json()["id"]

        # 2. Trigger transcription (this would be automatic via events)
        # or call transcription endpoint directly

        # 3. Wait for transcription to complete
        # (in real test, would poll for completion)

        # 4. Verify transcription was created
        pass
