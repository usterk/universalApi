"""Integration tests for documents API."""

import pytest
from httpx import AsyncClient
from uuid import uuid4


@pytest.mark.integration
@pytest.mark.asyncio
class TestDocumentTypes:
    """Tests for /api/v1/documents/types endpoint."""

    async def test_list_document_types_authenticated(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Authenticated user should get list of document types."""
        response = await async_client.get(
            "/api/v1/documents/types",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Each type should have required fields
        for doc_type in data:
            assert "id" in doc_type
            assert "name" in doc_type
            assert "display_name" in doc_type
            assert "registered_by" in doc_type
            assert "mime_types" in doc_type

    async def test_list_document_types_unauthenticated(
        self,
        async_client: AsyncClient,
    ):
        """Unauthenticated request should return 401."""
        response = await async_client.get("/api/v1/documents/types")
        assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
class TestDocumentsList:
    """Tests for /api/v1/documents endpoint."""

    async def test_list_documents_authenticated(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Authenticated user should get paginated document list."""
        response = await async_client.get(
            "/api/v1/documents",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "documents" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert isinstance(data["documents"], list)

    async def test_list_documents_with_pagination(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Should support pagination parameters."""
        response = await async_client.get(
            "/api/v1/documents",
            headers=auth_headers,
            params={"page": 1, "page_size": 5},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["page_size"] == 5

    async def test_list_documents_invalid_pagination(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Invalid pagination should return 422."""
        response = await async_client.get(
            "/api/v1/documents",
            headers=auth_headers,
            params={"page": 0},  # page must be >= 1
        )

        assert response.status_code == 422

    async def test_list_documents_page_size_limit(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Page size over 100 should return 422."""
        response = await async_client.get(
            "/api/v1/documents",
            headers=auth_headers,
            params={"page_size": 101},
        )

        assert response.status_code == 422

    async def test_list_documents_unauthenticated(
        self,
        async_client: AsyncClient,
    ):
        """Unauthenticated request should return 401."""
        response = await async_client.get("/api/v1/documents")
        assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
class TestDocumentGet:
    """Tests for /api/v1/documents/{document_id} endpoint."""

    async def test_get_document_not_found(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Non-existent document should return 404."""
        fake_id = str(uuid4())
        response = await async_client.get(
            f"/api/v1/documents/{fake_id}",
            headers=auth_headers,
        )

        assert response.status_code == 404

    async def test_get_document_invalid_uuid(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Invalid UUID should return 422."""
        response = await async_client.get(
            "/api/v1/documents/not-a-uuid",
            headers=auth_headers,
        )

        assert response.status_code == 422

    async def test_get_document_unauthenticated(
        self,
        async_client: AsyncClient,
    ):
        """Unauthenticated request should return 401."""
        fake_id = str(uuid4())
        response = await async_client.get(f"/api/v1/documents/{fake_id}")
        assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
class TestDocumentChildren:
    """Tests for /api/v1/documents/{document_id}/children endpoint."""

    async def test_get_children_not_found(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Non-existent parent document should return 404."""
        fake_id = str(uuid4())
        response = await async_client.get(
            f"/api/v1/documents/{fake_id}/children",
            headers=auth_headers,
        )

        assert response.status_code == 404

    async def test_get_children_unauthenticated(
        self,
        async_client: AsyncClient,
    ):
        """Unauthenticated request should return 401."""
        fake_id = str(uuid4())
        response = await async_client.get(f"/api/v1/documents/{fake_id}/children")
        assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
class TestDocumentDelete:
    """Tests for DELETE /api/v1/documents/{document_id} endpoint."""

    async def test_delete_document_not_found(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Deleting non-existent document should return 404."""
        fake_id = str(uuid4())
        response = await async_client.delete(
            f"/api/v1/documents/{fake_id}",
            headers=auth_headers,
        )

        assert response.status_code == 404

    async def test_delete_document_unauthenticated(
        self,
        async_client: AsyncClient,
    ):
        """Unauthenticated request should return 401."""
        fake_id = str(uuid4())
        response = await async_client.delete(f"/api/v1/documents/{fake_id}")
        assert response.status_code == 401
