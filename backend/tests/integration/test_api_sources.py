"""Integration tests for sources API."""

import pytest
from httpx import AsyncClient
from uuid import uuid4


@pytest.mark.integration
@pytest.mark.asyncio
class TestSourcesList:
    """Tests for GET /api/v1/sources endpoint."""

    async def test_list_sources_authenticated(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Authenticated user should get paginated list of their sources."""
        response = await async_client.get(
            "/api/v1/sources",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        # API returns paginated response
        assert isinstance(data, dict)
        assert "items" in data
        assert isinstance(data["items"], list)
        assert "total" in data
        assert "page" in data
        assert "page_size" in data

    async def test_list_sources_unauthenticated(
        self,
        async_client: AsyncClient,
    ):
        """Unauthenticated request should return 401."""
        response = await async_client.get("/api/v1/sources")
        assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
class TestSourceCreate:
    """Tests for POST /api/v1/sources endpoint."""

    async def test_create_source_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Should create source with API key."""
        response = await async_client.post(
            "/api/v1/sources",
            headers=auth_headers,
            json={
                "name": "Test Device",
                "description": "A test device",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Device"
        assert data["description"] == "A test device"
        assert "api_key" in data  # Full key returned on create
        assert "api_key_prefix" in data
        assert data["is_active"] is True

    async def test_create_source_minimal(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Should create source with only required fields."""
        response = await async_client.post(
            "/api/v1/sources",
            headers=auth_headers,
            json={"name": "Minimal Source"},
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Minimal Source"
        assert data["description"] is None

    async def test_create_source_with_properties(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Should create source with custom properties."""
        response = await async_client.post(
            "/api/v1/sources",
            headers=auth_headers,
            json={
                "name": "Device with Props",
                "properties": {"device_type": "mobile", "os": "iOS"},
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["properties"]["device_type"] == "mobile"
        assert data["properties"]["os"] == "iOS"

    async def test_create_source_missing_name(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Missing name should return 422."""
        response = await async_client.post(
            "/api/v1/sources",
            headers=auth_headers,
            json={"description": "No name provided"},
        )

        assert response.status_code == 422

    async def test_create_source_unauthenticated(
        self,
        async_client: AsyncClient,
    ):
        """Unauthenticated request should return 401."""
        response = await async_client.post(
            "/api/v1/sources",
            json={"name": "Test"},
        )
        assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
class TestSourceGet:
    """Tests for GET /api/v1/sources/{source_id} endpoint."""

    async def test_get_source_not_found(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Non-existent source should return 404."""
        fake_id = str(uuid4())
        response = await async_client.get(
            f"/api/v1/sources/{fake_id}",
            headers=auth_headers,
        )

        assert response.status_code == 404

    async def test_get_source_invalid_uuid(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Invalid UUID should return 422."""
        response = await async_client.get(
            "/api/v1/sources/not-a-uuid",
            headers=auth_headers,
        )

        assert response.status_code == 422

    async def test_get_source_unauthenticated(
        self,
        async_client: AsyncClient,
    ):
        """Unauthenticated request should return 401."""
        fake_id = str(uuid4())
        response = await async_client.get(f"/api/v1/sources/{fake_id}")
        assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
class TestSourceUpdate:
    """Tests for PATCH /api/v1/sources/{source_id} endpoint."""

    async def test_update_source_not_found(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Updating non-existent source should return 404."""
        fake_id = str(uuid4())
        response = await async_client.patch(
            f"/api/v1/sources/{fake_id}",
            headers=auth_headers,
            json={"name": "Updated Name"},
        )

        assert response.status_code == 404

    async def test_update_source_unauthenticated(
        self,
        async_client: AsyncClient,
    ):
        """Unauthenticated request should return 401."""
        fake_id = str(uuid4())
        response = await async_client.patch(
            f"/api/v1/sources/{fake_id}",
            json={"name": "Updated"},
        )
        assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
class TestSourceDelete:
    """Tests for DELETE /api/v1/sources/{source_id} endpoint."""

    async def test_delete_source_not_found(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Deleting non-existent source should return 404."""
        fake_id = str(uuid4())
        response = await async_client.delete(
            f"/api/v1/sources/{fake_id}",
            headers=auth_headers,
        )

        assert response.status_code == 404

    async def test_delete_source_unauthenticated(
        self,
        async_client: AsyncClient,
    ):
        """Unauthenticated request should return 401."""
        fake_id = str(uuid4())
        response = await async_client.delete(f"/api/v1/sources/{fake_id}")
        assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
class TestSourceRegenerateKey:
    """Tests for POST /api/v1/sources/{source_id}/regenerate-key endpoint."""

    async def test_regenerate_key_not_found(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Regenerating key for non-existent source should return 404."""
        fake_id = str(uuid4())
        response = await async_client.post(
            f"/api/v1/sources/{fake_id}/regenerate-key",
            headers=auth_headers,
        )

        assert response.status_code == 404

    async def test_regenerate_key_unauthenticated(
        self,
        async_client: AsyncClient,
    ):
        """Unauthenticated request should return 401."""
        fake_id = str(uuid4())
        response = await async_client.post(f"/api/v1/sources/{fake_id}/regenerate-key")
        assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
class TestSourceCRUDFlow:
    """End-to-end test for source CRUD operations."""

    async def test_source_crud_flow(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test complete create-read-update-delete flow."""
        # 1. Create source
        create_response = await async_client.post(
            "/api/v1/sources",
            headers=auth_headers,
            json={
                "name": "CRUD Test Device",
                "description": "Testing CRUD operations",
            },
        )
        assert create_response.status_code == 201
        source_id = create_response.json()["id"]
        original_api_key = create_response.json()["api_key"]

        # 2. Read source
        get_response = await async_client.get(
            f"/api/v1/sources/{source_id}",
            headers=auth_headers,
        )
        assert get_response.status_code == 200
        assert get_response.json()["name"] == "CRUD Test Device"
        assert "api_key" not in get_response.json()  # Full key not returned on GET

        # 3. Update source
        update_response = await async_client.patch(
            f"/api/v1/sources/{source_id}",
            headers=auth_headers,
            json={
                "name": "Updated CRUD Device",
                "is_active": False,
            },
        )
        assert update_response.status_code == 200
        assert update_response.json()["name"] == "Updated CRUD Device"
        assert update_response.json()["is_active"] is False

        # 4. Regenerate API key
        regen_response = await async_client.post(
            f"/api/v1/sources/{source_id}/regenerate-key",
            headers=auth_headers,
        )
        assert regen_response.status_code == 200
        new_api_key = regen_response.json()["api_key"]
        assert new_api_key != original_api_key  # Key should be different

        # 5. Delete source
        delete_response = await async_client.delete(
            f"/api/v1/sources/{source_id}",
            headers=auth_headers,
        )
        assert delete_response.status_code == 204

        # 6. Verify deleted
        verify_response = await async_client.get(
            f"/api/v1/sources/{source_id}",
            headers=auth_headers,
        )
        assert verify_response.status_code == 404
