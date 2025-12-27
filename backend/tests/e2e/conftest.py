"""E2E test fixtures."""

import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

# Import shared fixtures
from tests.conftest import *  # noqa: F401, F403


@pytest_asyncio.fixture(autouse=True)
async def register_document_types(app, db_session: AsyncSession):
    """
    Register document types from plugins in the test database.

    This fixture runs automatically before each E2E test to ensure
    document types are available in the database.
    """
    from app.core.documents.models import DocumentType
    from app.core.plugins.registry import PluginRegistry
    from sqlalchemy import select

    # Get plugin registry from app state
    registry = PluginRegistry()

    # Collect document types from all plugins
    doc_types_data = registry.collect_document_types()

    # Register each document type in database
    for dt_data in doc_types_data:
        # Check if already exists
        result = await db_session.execute(
            select(DocumentType).where(DocumentType.name == dt_data["name"])
        )
        existing = result.scalar_one_or_none()

        if not existing:
            doc_type = DocumentType(
                name=dt_data["name"],
                display_name=dt_data["display_name"],
                mime_types=dt_data.get("mime_types", []),
                registered_by=dt_data["registered_by"],
                metadata_schema=dt_data.get("metadata_schema"),
            )
            db_session.add(doc_type)

    await db_session.commit()
    yield
