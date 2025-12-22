"""Integration tests for plugins API."""

import pytest
from httpx import AsyncClient
from uuid import uuid4


@pytest.mark.integration
@pytest.mark.asyncio
class TestPluginsList:
    """Tests for GET /api/v1/plugins endpoint."""

    async def test_list_plugins_authenticated(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Authenticated user should get list of plugins."""
        response = await async_client.get(
            "/api/v1/plugins",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        # Each plugin should have required fields
        for plugin in data:
            assert "name" in plugin
            assert "display_name" in plugin
            assert "version" in plugin
            assert "description" in plugin
            assert "is_enabled" in plugin
            assert "priority" in plugin
            assert "state" in plugin

    async def test_list_plugins_unauthenticated(
        self,
        async_client: AsyncClient,
    ):
        """Unauthenticated request should return 401."""
        response = await async_client.get("/api/v1/plugins")
        assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
class TestPluginGet:
    """Tests for GET /api/v1/plugins/{plugin_name} endpoint."""

    async def test_get_plugin_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Should get existing plugin details."""
        # First get list to find an existing plugin
        list_response = await async_client.get(
            "/api/v1/plugins",
            headers=auth_headers,
        )

        if list_response.status_code == 200 and list_response.json():
            plugin_name = list_response.json()[0]["name"]

            response = await async_client.get(
                f"/api/v1/plugins/{plugin_name}",
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["name"] == plugin_name

    async def test_get_plugin_not_found(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Non-existent plugin should return 404."""
        response = await async_client.get(
            "/api/v1/plugins/nonexistent_plugin",
            headers=auth_headers,
        )

        assert response.status_code == 404

    async def test_get_plugin_unauthenticated(
        self,
        async_client: AsyncClient,
    ):
        """Unauthenticated request should return 401."""
        response = await async_client.get("/api/v1/plugins/some_plugin")
        assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
class TestPluginEnable:
    """Tests for POST /api/v1/plugins/{plugin_name}/enable endpoint."""

    async def test_enable_plugin_requires_superuser(
        self,
        async_client: AsyncClient,
        auth_headers: dict,  # Regular user, not superuser
    ):
        """Regular user should get 403."""
        response = await async_client.post(
            "/api/v1/plugins/upload/enable",
            headers=auth_headers,
        )

        # Should be forbidden for non-superuser
        assert response.status_code == 403

    async def test_enable_plugin_as_superuser(
        self,
        async_client: AsyncClient,
        admin_auth_headers: dict,
    ):
        """Superuser should be able to enable plugin."""
        # First get list to find an existing plugin
        list_response = await async_client.get(
            "/api/v1/plugins",
            headers=admin_auth_headers,
        )

        if list_response.status_code == 200 and list_response.json():
            plugin_name = list_response.json()[0]["name"]

            response = await async_client.post(
                f"/api/v1/plugins/{plugin_name}/enable",
                headers=admin_auth_headers,
            )

            assert response.status_code == 200

    async def test_enable_plugin_not_found(
        self,
        async_client: AsyncClient,
        admin_auth_headers: dict,
    ):
        """Enabling non-existent plugin should return 404."""
        response = await async_client.post(
            "/api/v1/plugins/nonexistent_plugin/enable",
            headers=admin_auth_headers,
        )

        assert response.status_code == 404

    async def test_enable_plugin_unauthenticated(
        self,
        async_client: AsyncClient,
    ):
        """Unauthenticated request should return 401."""
        response = await async_client.post("/api/v1/plugins/upload/enable")
        assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
class TestPluginDisable:
    """Tests for POST /api/v1/plugins/{plugin_name}/disable endpoint."""

    async def test_disable_plugin_requires_superuser(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Regular user should get 403."""
        response = await async_client.post(
            "/api/v1/plugins/upload/disable",
            headers=auth_headers,
        )

        assert response.status_code == 403

    async def test_disable_plugin_not_found(
        self,
        async_client: AsyncClient,
        admin_auth_headers: dict,
    ):
        """Disabling non-existent plugin should return 404."""
        response = await async_client.post(
            "/api/v1/plugins/nonexistent_plugin/disable",
            headers=admin_auth_headers,
        )

        assert response.status_code == 404

    async def test_disable_plugin_unauthenticated(
        self,
        async_client: AsyncClient,
    ):
        """Unauthenticated request should return 401."""
        response = await async_client.post("/api/v1/plugins/upload/disable")
        assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
class TestPluginFilters:
    """Tests for plugin filters endpoints."""

    async def test_list_filters_authenticated(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Should list plugin filters."""
        response = await async_client.get(
            "/api/v1/plugins/upload/filters",
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_list_filters_unauthenticated(
        self,
        async_client: AsyncClient,
    ):
        """Unauthenticated request should return 401."""
        response = await async_client.get("/api/v1/plugins/upload/filters")
        assert response.status_code == 401

    async def test_create_filter_requires_superuser(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Regular user should get 403."""
        response = await async_client.post(
            "/api/v1/plugins/upload/filters",
            headers=auth_headers,
            json={
                "filter_type": "source",
                "operator": "equals",
                "value": "test-source",
            },
        )

        assert response.status_code == 403

    async def test_delete_filter_requires_superuser(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Regular user should get 403."""
        fake_filter_id = str(uuid4())
        response = await async_client.delete(
            f"/api/v1/plugins/upload/filters/{fake_filter_id}",
            headers=auth_headers,
        )

        assert response.status_code == 403


@pytest.mark.integration
@pytest.mark.asyncio
class TestPluginJobs:
    """Tests for plugin jobs endpoints."""

    async def test_list_jobs_authenticated(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Should list processing jobs."""
        response = await async_client.get(
            "/api/v1/plugins/jobs",
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert isinstance(response.json(), list)

    async def test_list_jobs_with_status_filter(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Should filter jobs by status."""
        response = await async_client.get(
            "/api/v1/plugins/jobs",
            headers=auth_headers,
            params={"status": "completed"},
        )

        assert response.status_code == 200

    async def test_list_jobs_with_plugin_filter(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Should filter jobs by plugin name."""
        response = await async_client.get(
            "/api/v1/plugins/jobs",
            headers=auth_headers,
            params={"plugin_name": "audio_transcription"},
        )

        assert response.status_code == 200

    async def test_list_jobs_unauthenticated(
        self,
        async_client: AsyncClient,
    ):
        """Unauthenticated request should return 401."""
        response = await async_client.get("/api/v1/plugins/jobs")
        assert response.status_code == 401

    async def test_get_job_not_found(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Non-existent job should return 404."""
        fake_id = str(uuid4())
        response = await async_client.get(
            f"/api/v1/plugins/jobs/{fake_id}",
            headers=auth_headers,
        )

        assert response.status_code == 404

    async def test_get_job_unauthenticated(
        self,
        async_client: AsyncClient,
    ):
        """Unauthenticated request should return 401."""
        fake_id = str(uuid4())
        response = await async_client.get(f"/api/v1/plugins/jobs/{fake_id}")
        assert response.status_code == 401

    async def test_cancel_job_not_found(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Cancelling non-existent job should return 404."""
        fake_id = str(uuid4())
        response = await async_client.post(
            f"/api/v1/plugins/jobs/{fake_id}/cancel",
            headers=auth_headers,
        )

        assert response.status_code == 404

    async def test_cancel_job_unauthenticated(
        self,
        async_client: AsyncClient,
    ):
        """Unauthenticated request should return 401."""
        fake_id = str(uuid4())
        response = await async_client.post(f"/api/v1/plugins/jobs/{fake_id}/cancel")
        assert response.status_code == 401
