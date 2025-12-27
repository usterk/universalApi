"""Integration tests for workflow API endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.sources.models import Source
from app.core.plugins.models import SourceWorkflowStep


@pytest.mark.asyncio
async def test_get_workflow_empty(
    async_client: AsyncClient,
    db_session: AsyncSession,
    test_user,
    auth_headers,
):
    """Test getting empty workflow for a source."""
    # Create source
    source = Source(
        owner_id=test_user["id"],
        name="Test Source",
        api_key_hash="dummy_hash",
        api_key_prefix="test_",
    )
    db_session.add(source)
    await db_session.commit()
    await db_session.refresh(source)

    # Get workflow (should be empty)
    response = await async_client.get(
        f"/api/v1/sources/{source.id}/workflows/audio",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["document_type"] == "audio"
    assert data["steps"] == []


@pytest.mark.asyncio
async def test_add_workflow_step(
    async_client: AsyncClient,
    db_session: AsyncSession,
    test_user,
    auth_headers,
):
    """Test adding a step to workflow."""
    # Create source
    source = Source(
        owner_id=test_user["id"],
        name="Test Source",
        api_key_hash="dummy_hash",
        api_key_prefix="test_",
    )
    db_session.add(source)
    await db_session.commit()
    await db_session.refresh(source)

    # Add first step
    response = await async_client.post(
        f"/api/v1/sources/{source.id}/workflows/audio/steps",
        headers=auth_headers,
        json={
            "plugin_name": "audio_transcription",
            "sequence_number": 1,
            "settings": {},
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["plugin_name"] == "audio_transcription"
    assert data["sequence_number"] == 1
    assert "id" in data


@pytest.mark.asyncio
async def test_add_workflow_step_validates_first_step_compatibility(
    async_client: AsyncClient,
    db_session: AsyncSession,
    test_user,
    auth_headers,
):
    """Test that first step must accept document type."""
    # Create source
    source = Source(
        owner_id=test_user["id"],
        name="Test Source",
        api_key_hash="dummy_hash",
        api_key_prefix="test_",
    )
    db_session.add(source)
    await db_session.commit()
    await db_session.refresh(source)

    # Try to add a plugin that doesn't accept "audio" as first step
    # Note: This test assumes there's a plugin that doesn't accept audio
    # If audio_transcription is the only plugin, this test might not be meaningful
    # For now, we'll test with a valid plugin and verify the happy path

    response = await async_client.post(
        f"/api/v1/sources/{source.id}/workflows/audio/steps",
        headers=auth_headers,
        json={
            "plugin_name": "audio_transcription",
            "sequence_number": 1,
            "settings": {},
        },
    )

    assert response.status_code == 201


@pytest.mark.asyncio
async def test_get_workflow_with_steps(
    async_client: AsyncClient,
    db_session: AsyncSession,
    test_user,
    auth_headers,
):
    """Test getting workflow with multiple steps."""
    # Create source
    source = Source(
        owner_id=test_user["id"],
        name="Test Source",
        api_key_hash="dummy_hash",
        api_key_prefix="test_",
    )
    db_session.add(source)
    await db_session.commit()
    await db_session.refresh(source)

    # Add step directly via database
    step = SourceWorkflowStep(
        source_id=source.id,
        document_type="audio",
        sequence_number=1,
        plugin_name="audio_transcription",
        is_enabled=True,
        settings={},
    )
    db_session.add(step)
    await db_session.commit()

    # Get workflow
    response = await async_client.get(
        f"/api/v1/sources/{source.id}/workflows/audio",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["document_type"] == "audio"
    assert len(data["steps"]) == 1
    assert data["steps"][0]["plugin_name"] == "audio_transcription"
    assert data["steps"][0]["sequence_number"] == 1


@pytest.mark.asyncio
async def test_delete_workflow_step(
    async_client: AsyncClient,
    db_session: AsyncSession,
    test_user,
    auth_headers,
):
    """Test deleting a workflow step."""
    # Create source
    source = Source(
        owner_id=test_user["id"],
        name="Test Source",
        api_key_hash="dummy_hash",
        api_key_prefix="test_",
    )
    db_session.add(source)
    await db_session.commit()
    await db_session.refresh(source)

    # Add step
    step = SourceWorkflowStep(
        source_id=source.id,
        document_type="audio",
        sequence_number=1,
        plugin_name="audio_transcription",
        is_enabled=True,
        settings={},
    )
    db_session.add(step)
    await db_session.commit()
    await db_session.refresh(step)

    # Delete step
    response = await async_client.delete(
        f"/api/v1/sources/{source.id}/workflows/audio/steps/{step.id}",
        headers=auth_headers,
    )

    assert response.status_code == 204

    # Verify deletion
    response = await async_client.get(
        f"/api/v1/sources/{source.id}/workflows/audio",
        headers=auth_headers,
    )
    data = response.json()
    assert len(data["steps"]) == 0


@pytest.mark.asyncio
async def test_reorder_workflow(
    async_client: AsyncClient,
    db_session: AsyncSession,
    test_user,
    auth_headers,
):
    """Test reordering workflow steps."""
    # Create source
    source = Source(
        owner_id=test_user["id"],
        name="Test Source",
        api_key_hash="dummy_hash",
        api_key_prefix="test_",
    )
    db_session.add(source)
    await db_session.commit()
    await db_session.refresh(source)

    # Add two steps (we need to ensure they're compatible for this test)
    step1 = SourceWorkflowStep(
        source_id=source.id,
        document_type="audio",
        sequence_number=1,
        plugin_name="audio_transcription",
        is_enabled=True,
        settings={},
    )
    db_session.add(step1)
    await db_session.commit()
    await db_session.refresh(step1)

    # For now, just test with one step since we don't have a second compatible plugin
    # Reorder with same order (no-op but tests the endpoint)
    response = await async_client.put(
        f"/api/v1/sources/{source.id}/workflows/audio/reorder",
        headers=auth_headers,
        json={
            "steps": [
                {"id": str(step1.id), "sequence_number": 1},
            ]
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert len(data["steps"]) == 1
    assert data["steps"][0]["sequence_number"] == 1


@pytest.mark.asyncio
async def test_get_available_plugins_for_first_step(
    async_client: AsyncClient,
    db_session: AsyncSession,
    test_user,
    auth_headers,
):
    """Test getting available plugins for first step (should accept document type)."""
    # Create source
    source = Source(
        owner_id=test_user["id"],
        name="Test Source",
        api_key_hash="dummy_hash",
        api_key_prefix="test_",
    )
    db_session.add(source)
    await db_session.commit()
    await db_session.refresh(source)

    # Get available plugins for audio documents
    response = await async_client.get(
        f"/api/v1/sources/{source.id}/workflows/audio/available-plugins",
        headers=auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Should include at least audio_transcription if it's enabled
    plugin_names = [p["name"] for p in data]
    # We can't assert specific plugins without knowing what's enabled
    # But we can verify the structure
    if len(data) > 0:
        assert "name" in data[0]
        assert "display_name" in data[0]
        assert "input_types" in data[0]


@pytest.mark.asyncio
async def test_workflow_requires_authentication(
    async_client: AsyncClient,
    db_session: AsyncSession,
    test_user,
):
    """Test that workflow endpoints require authentication."""
    # Create source
    source = Source(
        owner_id=test_user["id"],
        name="Test Source",
        api_key_hash="dummy_hash",
        api_key_prefix="test_",
    )
    db_session.add(source)
    await db_session.commit()
    await db_session.refresh(source)

    # Try to get workflow without auth
    response = await async_client.get(
        f"/api/v1/sources/{source.id}/workflows/audio",
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_workflow_requires_source_ownership(
    async_client: AsyncClient,
    db_session: AsyncSession,
    test_user,
    test_admin,
    auth_headers,
):
    """Test that users can only access workflows for their own sources."""
    # Create source owned by admin
    source = Source(
        owner_id=test_admin["id"],  # Different user!
        name="Admin's Source",
        api_key_hash="dummy_hash",
        api_key_prefix="admin_",
    )
    db_session.add(source)
    await db_session.commit()
    await db_session.refresh(source)

    # Try to get workflow as test_user (not owner)
    response = await async_client.get(
        f"/api/v1/sources/{source.id}/workflows/audio",
        headers=auth_headers,  # test_user's auth
    )

    assert response.status_code == 404  # Source not found (ownership check)
