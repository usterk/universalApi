"""End-to-end tests for Upload plugin."""

import pytest
from httpx import AsyncClient


@pytest.mark.e2e
@pytest.mark.plugin
@pytest.mark.asyncio
class TestUploadE2E:
    """E2E tests for complete upload workflow."""

    async def test_upload_text_file(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        sample_upload_file: bytes,
    ):
        """Upload text file should create document."""
        response = await async_client.post(
            "/api/v1/plugins/upload/files",
            headers=auth_headers,
            files={
                "file": ("test.txt", sample_upload_file, "text/plain"),
            },
        )

        assert response.status_code in [200, 201]
        data = response.json()
        assert "id" in data

    async def test_upload_audio_file(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        sample_audio_upload: tuple,
    ):
        """Upload audio file should create document with correct type."""
        content, filename, content_type = sample_audio_upload

        response = await async_client.post(
            "/api/v1/plugins/upload/files",
            headers=auth_headers,
            files={
                "file": (filename, content, content_type),
            },
        )

        assert response.status_code in [200, 201]
        data = response.json()
        assert "id" in data
        assert data["document_type"] == "audio", "Should detect audio type from content_type"

    async def test_upload_audio_file_without_mime_type(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        sample_audio_upload: tuple,
    ):
        """Upload audio file WITHOUT content_type should auto-detect as audio.

        This test ensures MIME type detection works even when HTTP headers
        don't provide correct content_type (e.g., curl uploads).
        """
        content, filename, _ = sample_audio_upload  # Ignore provided content_type

        response = await async_client.post(
            "/api/v1/plugins/upload/files",
            headers=auth_headers,
            files={
                # Upload with application/octet-stream (default when MIME not specified)
                "file": (filename, content, "application/octet-stream"),
            },
        )

        assert response.status_code in [200, 201]
        data = response.json()
        assert "id" in data
        assert data["document_type"] == "audio", "Should auto-detect audio type from content even without HTTP content_type"

    async def test_upload_requires_auth(
        self,
        async_client: AsyncClient,
        sample_upload_file: bytes,
    ):
        """Upload should require authentication."""
        response = await async_client.post(
            "/api/v1/plugins/upload/files",
            files={
                "file": ("test.txt", sample_upload_file, "text/plain"),
            },
        )

        assert response.status_code == 401

    async def test_upload_without_file_fails(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Upload without file should fail."""
        response = await async_client.post(
            "/api/v1/plugins/upload/files",
            headers=auth_headers,
        )

        assert response.status_code == 422


@pytest.mark.e2e
@pytest.mark.plugin
@pytest.mark.asyncio
class TestUploadDocumentRetrieval:
    """E2E tests for document retrieval after upload."""

    async def test_get_uploaded_document(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        sample_upload_file: bytes,
    ):
        """Should be able to retrieve uploaded document metadata."""
        # First upload a file
        upload_response = await async_client.post(
            "/api/v1/plugins/upload/files",
            headers=auth_headers,
            files={
                "file": ("test.txt", sample_upload_file, "text/plain"),
            },
        )

        assert upload_response.status_code in [200, 201]
        document_id = upload_response.json()["id"]

        # Then retrieve it
        get_response = await async_client.get(
            f"/api/v1/documents/{document_id}",
            headers=auth_headers,
        )

        assert get_response.status_code == 200
        data = get_response.json()
        assert data["id"] == document_id

    async def test_list_user_documents(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Should be able to list user's documents."""
        response = await async_client.get(
            "/api/v1/documents",
            headers=auth_headers,
        )

        assert response.status_code == 200
        # Response could be list or paginated object
        data = response.json()
        assert isinstance(data, (list, dict))


@pytest.mark.e2e
@pytest.mark.plugin
@pytest.mark.asyncio
class TestUnicodeFilenames:
    """E2E tests for Unicode filename handling (RFC 2231)."""

    async def test_download_file_with_emoji_filename(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test downloading file with emoji in filename."""
        # Create a test file with emoji
        file_content = b"Test content with emoji"
        filename = "test_file_🎯_emoji.txt"

        # Upload file
        upload_response = await async_client.post(
            "/api/v1/plugins/upload/files",
            files={"file": (filename, file_content, "text/plain")},
            headers=auth_headers,
        )
        assert upload_response.status_code in [200, 201]
        document_id = upload_response.json()["id"]

        # Download file
        download_response = await async_client.get(
            f"/api/v1/plugins/upload/files/{document_id}/content",
            headers=auth_headers,
        )
        assert download_response.status_code == 200
        assert download_response.content == file_content

        # Check Content-Disposition header uses RFC 2231 encoding
        content_disp = download_response.headers.get("content-disposition")
        assert content_disp is not None
        assert "filename*=UTF-8''" in content_disp
        # Emoji will be percent-encoded
        assert "test_file_" in content_disp

    async def test_download_file_with_unicode_accents(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test downloading file with accented characters in filename."""
        file_content = b"Test content"
        filename = "café_résumé_naïve.txt"

        # Upload file
        upload_response = await async_client.post(
            "/api/v1/plugins/upload/files",
            files={"file": (filename, file_content, "text/plain")},
            headers=auth_headers,
        )
        assert upload_response.status_code in [200, 201]
        document_id = upload_response.json()["id"]

        # Download file
        download_response = await async_client.get(
            f"/api/v1/plugins/upload/files/{document_id}/content",
            headers=auth_headers,
        )
        assert download_response.status_code == 200
        assert download_response.content == file_content

        # Check Content-Disposition header
        content_disp = download_response.headers.get("content-disposition")
        assert content_disp is not None
        assert "filename*=UTF-8''" in content_disp

    async def test_download_file_ascii_filename(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test downloading file with ASCII-only filename uses simple format."""
        file_content = b"Test content"
        filename = "simple_test_file.txt"

        # Upload file
        upload_response = await async_client.post(
            "/api/v1/plugins/upload/files",
            files={"file": (filename, file_content, "text/plain")},
            headers=auth_headers,
        )
        assert upload_response.status_code in [200, 201]
        document_id = upload_response.json()["id"]

        # Download file
        download_response = await async_client.get(
            f"/api/v1/plugins/upload/files/{document_id}/content",
            headers=auth_headers,
        )
        assert download_response.status_code == 200

        # ASCII filenames should use simple quoted format
        content_disp = download_response.headers.get("content-disposition")
        assert content_disp is not None
        assert f'filename="{filename}"' in content_disp
        # Should NOT use RFC 2231 format for ASCII names
        assert "filename*=" not in content_disp
