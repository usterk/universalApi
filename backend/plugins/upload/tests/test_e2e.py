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
