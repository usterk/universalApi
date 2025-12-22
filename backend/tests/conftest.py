"""
Shared pytest fixtures for UniversalAPI tests.

These fixtures are available to all tests in the project, including plugin tests.

Usage in plugin tests:
    # In plugins/{name}/tests/conftest.py
    from tests.conftest import *  # noqa: F401, F403

Test categories:
    - Unit tests: Use mocked dependencies, no database
    - Integration tests: Use test database (docker-compose.test.yml)
    - E2E tests: Full application with test database

Database:
    Tests use a separate PostgreSQL instance on port 5433.
    Start with: make test-db-up
    Stop with: make test-db-down
"""

import os
from collections.abc import AsyncGenerator
from typing import Any
from uuid import uuid4

import pytest
import pytest_asyncio
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

# =============================================================================
# Environment Setup
# =============================================================================

# Load .env file FIRST so environment variables are available for skipif decorators
load_dotenv()

# Override settings BEFORE importing app modules
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://universalapi_test:universalapi_test@localhost:5433/universalapi_test",
)
os.environ.setdefault(
    "DATABASE_URL_SYNC",
    "postgresql://universalapi_test:universalapi_test@localhost:5433/universalapi_test",
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6380/0")
os.environ.setdefault("CELERY_BROKER_URL", "redis://localhost:6380/1")
os.environ.setdefault("CELERY_RESULT_BACKEND", "redis://localhost:6380/2")
os.environ.setdefault("APP_ENV", "testing")
os.environ.setdefault("DEBUG", "false")
os.environ.setdefault("LOG_LEVEL", "WARNING")

# Now import app modules
from app.config import Settings, get_settings  # noqa: E402
from app.core.database.base import Base  # noqa: E402
from app.core.database.session import get_db  # noqa: E402

# Import all models to register them with Base.metadata
from app.core.users.models import User, Role, Permission  # noqa: E402, F401
from app.core.sources.models import Source  # noqa: E402, F401
from app.core.documents.models import Document, DocumentType  # noqa: E402, F401
from app.core.plugins.models import PluginConfig, PluginFilter, ProcessingJob  # noqa: E402, F401


# =============================================================================
# Settings Fixtures
# =============================================================================


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Get test settings instance."""
    return Settings(
        database_url="postgresql+asyncpg://universalapi_test:universalapi_test@localhost:5433/universalapi_test",
        database_url_sync="postgresql://universalapi_test:universalapi_test@localhost:5433/universalapi_test",
        redis_url="redis://localhost:6380/0",
        celery_broker_url="redis://localhost:6380/1",
        celery_result_backend="redis://localhost:6380/2",
        app_env="testing",
        debug=False,
        log_level="WARNING",
    )


# =============================================================================
# Database Fixtures
# =============================================================================


@pytest_asyncio.fixture
async def test_engine(test_settings: Settings):
    """Create test database engine.

    Uses NullPool to avoid event loop conflicts with asyncpg.
    Each connection is created fresh in the current event loop context.
    """
    engine = create_async_engine(
        test_settings.database_url,
        echo=False,
        poolclass=NullPool,
    )
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def setup_database(test_engine):
    """Create all tables in test database.

    Note: This recreates tables for each test function.
    For better performance, could be made session-scoped,
    but function scope avoids event loop conflicts.
    """
    async with test_engine.begin() as conn:
        # Drop all tables first
        await conn.run_sync(Base.metadata.drop_all)
        # Then create them fresh
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Clean up after test
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def test_session_factory(test_engine):
    """Create session factory for tests."""
    return async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )


@pytest_asyncio.fixture
async def db_session(
    test_session_factory,
    setup_database,
) -> AsyncGenerator[AsyncSession, None]:
    """
    Create a fresh database session for each test.

    Allows the endpoint to commit its own transactions.
    Session is cleaned up after the test completes.
    """
    async with test_session_factory() as session:
        yield session
        # Try to rollback any uncommitted changes
        if session.in_transaction():
            await session.rollback()
        await session.close()


@pytest_asyncio.fixture
async def clean_db_session(
    test_session_factory,
    setup_database,
) -> AsyncGenerator[AsyncSession, None]:
    """
    Create a database session that truncates tables after test.

    Use for tests that need committed data (e.g., testing queries).
    """
    async with test_session_factory() as session:
        yield session

    # Clean up all tables after test
    async with test_session_factory() as cleanup_session:
        async with cleanup_session.begin():
            result = await cleanup_session.execute(
                text("""
                    SELECT tablename FROM pg_tables
                    WHERE schemaname = 'public'
                    AND tablename != 'alembic_version'
                """)
            )
            tables = [row[0] for row in result.fetchall()]

            for table in tables:
                await cleanup_session.execute(text(f'TRUNCATE TABLE "{table}" CASCADE'))


# =============================================================================
# Application Fixtures
# =============================================================================


@pytest_asyncio.fixture
async def app(setup_database, test_engine, test_session_factory) -> FastAPI:
    """Create test application instance.

    Patches the application's database engine and session factory
    to use test database instead of production database.

    Also manually initializes plugin registry and event bus for testing
    since lifespan events aren't automatically triggered in tests.
    """
    from app.main import create_app
    import app.core.database.session as db_session_module
    from app.core.events.bus import EventBus
    from app.core.plugins.registry import PluginRegistry
    from app.core.plugins.loader import PluginLoader

    # Replace module-level engine and session factory with test versions
    original_engine = db_session_module.engine
    original_factory = db_session_module.async_session_factory

    db_session_module.engine = test_engine
    db_session_module.async_session_factory = test_session_factory

    # Reset plugin registry singleton to avoid cross-test contamination
    PluginRegistry._instance = None

    app_instance = create_app()

    # Manually initialize plugin system (normally done in lifespan)
    event_bus = EventBus()
    event_bus.set_db_session_factory(test_session_factory)
    registry = PluginRegistry()

    # Load plugins
    loader = PluginLoader(registry, event_bus)
    discovered = loader.discover()
    plugin_settings: dict[str, dict] = {}
    await loader.load_all(plugin_settings)

    # Mount plugin routers
    for plugin_name, router in registry.collect_routers():
        app_instance.include_router(
            router,
            prefix=f"/api/v1/plugins/{plugin_name}",
            tags=[f"plugin:{plugin_name}"],
        )

    # Register event handlers
    for plugin in registry.get_active_plugins():
        handlers = plugin.get_event_handlers()
        for event_type, handler_list in handlers.items():
            for handler in handler_list:
                event_bus.subscribe(event_type, handler)

    # Call startup hooks
    for plugin in registry.get_active_plugins():
        await plugin.on_startup()

    # Store in app state (this is what the endpoints expect)
    app_instance.state.event_bus = event_bus
    app_instance.state.plugin_registry = registry

    yield app_instance

    # Cleanup: call shutdown hooks
    for plugin in registry.get_active_plugins():
        await plugin.on_shutdown()

    # Reset singleton again after test
    PluginRegistry._instance = None

    # Restore original engine and factory
    db_session_module.engine = original_engine
    db_session_module.async_session_factory = original_factory


@pytest.fixture
def client(app: FastAPI, db_session: AsyncSession) -> TestClient:
    """Create synchronous test client."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def async_client(
    app: FastAPI,
    db_session: AsyncSession,
) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client."""

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# =============================================================================
# Authentication Fixtures
# =============================================================================


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession) -> dict[str, Any]:
    """Create a test user."""
    from app.core.auth.password import hash_password
    from app.core.users.models import User, Role

    # Get or create user role
    result = await db_session.execute(
        text("SELECT id FROM roles WHERE name = 'user' LIMIT 1")
    )
    role_row = result.fetchone()

    if not role_row:
        role = Role(name="user", description="Regular user")
        db_session.add(role)
        await db_session.flush()
        role_id = role.id
    else:
        role_id = role_row[0]

    user_id = uuid4()
    email = f"test_{uuid4().hex[:8]}@example.com"

    user = User(
        id=user_id,
        email=email,
        hashed_password=hash_password("testpassword123"),
        full_name="Test User",
        is_active=True,
        is_superuser=False,
        role_id=role_id,
    )
    db_session.add(user)
    await db_session.flush()

    return {
        "id": str(user.id),
        "email": email,
        "password": "testpassword123",
        "full_name": "Test User",
    }


@pytest_asyncio.fixture
async def test_admin(db_session: AsyncSession) -> dict[str, Any]:
    """Create a test admin user."""
    from app.core.auth.password import hash_password
    from app.core.users.models import User, Role

    # Get or create admin role
    result = await db_session.execute(
        text("SELECT id FROM roles WHERE name = 'admin' LIMIT 1")
    )
    role_row = result.fetchone()

    if not role_row:
        role = Role(name="admin", description="Administrator")
        db_session.add(role)
        await db_session.flush()
        role_id = role.id
    else:
        role_id = role_row[0]

    user_id = uuid4()
    email = f"admin_{uuid4().hex[:8]}@example.com"

    user = User(
        id=user_id,
        email=email,
        hashed_password=hash_password("adminpassword123"),
        full_name="Test Admin",
        is_active=True,
        is_superuser=True,
        role_id=role_id,
    )
    db_session.add(user)
    await db_session.flush()

    return {
        "id": str(user.id),
        "email": email,
        "password": "adminpassword123",
        "full_name": "Test Admin",
    }


@pytest_asyncio.fixture
async def auth_headers(async_client: AsyncClient, test_user: dict) -> dict[str, str]:
    """Get authentication headers for test user."""
    response = await async_client.post(
        "/api/v1/auth/login",
        json={
            "email": test_user["email"],
            "password": test_user["password"],
        },
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    tokens = response.json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}


@pytest_asyncio.fixture
async def admin_auth_headers(
    async_client: AsyncClient, test_admin: dict
) -> dict[str, str]:
    """Get authentication headers for admin user."""
    response = await async_client.post(
        "/api/v1/auth/login",
        json={
            "email": test_admin["email"],
            "password": test_admin["password"],
        },
    )
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    tokens = response.json()
    return {"Authorization": f"Bearer {tokens['access_token']}"}


# =============================================================================
# Mock Fixtures
# =============================================================================


@pytest.fixture
def mock_event_bus():
    """Create a mock event bus for unit tests."""
    from unittest.mock import AsyncMock, MagicMock

    bus = MagicMock()
    bus.emit = AsyncMock()
    bus.emit_sync = AsyncMock()
    bus.subscribe = MagicMock()
    bus.unsubscribe = MagicMock()
    bus.get_recent_events = MagicMock(return_value=[])
    bus.register_sse_client = MagicMock()
    bus.unregister_sse_client = MagicMock()

    return bus


@pytest.fixture
def mock_plugin_registry():
    """Create a mock plugin registry for unit tests."""
    from unittest.mock import MagicMock

    registry = MagicMock()
    registry.get_active_plugins = MagicMock(return_value=[])
    registry.get_plugin = MagicMock(return_value=None)
    registry.is_loaded = MagicMock(return_value=False)

    return registry


# =============================================================================
# File Fixtures
# =============================================================================


@pytest.fixture
def sample_audio_file() -> bytes:
    """Return minimal valid MP3 file bytes (silence)."""
    # Minimal valid MP3 frame
    return bytes([0xFF, 0xFB, 0x90, 0x00] + [0x00] * 100)


@pytest.fixture
def sample_image_file() -> bytes:
    """Return minimal valid PNG file bytes (1x1 transparent)."""
    return bytes(
        [
            0x89,
            0x50,
            0x4E,
            0x47,
            0x0D,
            0x0A,
            0x1A,
            0x0A,  # PNG signature
            0x00,
            0x00,
            0x00,
            0x0D,
            0x49,
            0x48,
            0x44,
            0x52,  # IHDR
            0x00,
            0x00,
            0x00,
            0x01,
            0x00,
            0x00,
            0x00,
            0x01,  # 1x1
            0x08,
            0x06,
            0x00,
            0x00,
            0x00,
            0x1F,
            0x15,
            0xC4,
            0x89,
            0x00,
            0x00,
            0x00,
            0x0A,
            0x49,
            0x44,
            0x41,
            0x54,  # IDAT
            0x78,
            0x9C,
            0x63,
            0x00,
            0x01,
            0x00,
            0x00,
            0x05,
            0x00,
            0x01,
            0x0D,
            0x0A,
            0x2D,
            0xB4,
            0x00,
            0x00,
            0x00,
            0x00,
            0x49,
            0x45,
            0x4E,
            0x44,  # IEND
            0xAE,
            0x42,
            0x60,
            0x82,
        ]
    )


@pytest.fixture
def sample_text_file() -> bytes:
    """Return sample text file bytes."""
    return b"Hello, this is a test file content.\nLine 2.\nLine 3."


@pytest.fixture
def sample_json_file() -> bytes:
    """Return sample JSON file bytes."""
    import json

    return json.dumps({"test": "data", "number": 42, "nested": {"key": "value"}}).encode()
