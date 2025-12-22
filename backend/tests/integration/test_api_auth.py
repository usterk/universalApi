"""Integration tests for authentication API."""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.asyncio
class TestAuthLogin:
    """Tests for /api/v1/auth/login endpoint."""

    async def test_login_success(
        self,
        async_client: AsyncClient,
        test_user: dict,
    ):
        """Valid credentials should return tokens."""
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user["email"],
                "password": test_user["password"],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(
        self,
        async_client: AsyncClient,
        test_user: dict,
    ):
        """Wrong password should return 401."""
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user["email"],
                "password": "wrongpassword",
            },
        )

        assert response.status_code == 401

    async def test_login_nonexistent_user(
        self,
        async_client: AsyncClient,
    ):
        """Nonexistent user should return 401."""
        response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "somepassword",
            },
        )

        assert response.status_code == 401

    async def test_login_missing_credentials(
        self,
        async_client: AsyncClient,
    ):
        """Missing credentials should return 422."""
        response = await async_client.post(
            "/api/v1/auth/login",
            json={},
        )

        assert response.status_code == 422


@pytest.mark.integration
@pytest.mark.asyncio
class TestAuthMe:
    """Tests for /api/v1/auth/me endpoint."""

    async def test_me_authenticated(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_user: dict,
    ):
        """Authenticated user should get their profile."""
        response = await async_client.get(
            "/api/v1/auth/me",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user["email"]
        assert data["full_name"] == test_user["full_name"]

    async def test_me_unauthenticated(
        self,
        async_client: AsyncClient,
    ):
        """Unauthenticated request should return 401."""
        response = await async_client.get("/api/v1/auth/me")

        assert response.status_code == 401

    async def test_me_invalid_token(
        self,
        async_client: AsyncClient,
    ):
        """Invalid token should return 401."""
        response = await async_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalidtoken"},
        )

        assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.asyncio
class TestAuthRefresh:
    """Tests for /api/v1/auth/refresh endpoint."""

    async def test_refresh_token_success(
        self,
        async_client: AsyncClient,
        test_user: dict,
    ):
        """Valid refresh token should return new tokens."""
        # First login to get tokens
        login_response = await async_client.post(
            "/api/v1/auth/login",
            json={
                "email": test_user["email"],
                "password": test_user["password"],
            },
        )
        tokens = login_response.json()

        # Use refresh token to get new access token
        response = await async_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]},
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_refresh_token_invalid(
        self,
        async_client: AsyncClient,
    ):
        """Invalid refresh token should return 401."""
        response = await async_client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid_refresh_token"},
        )

        assert response.status_code == 401
