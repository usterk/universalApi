"""Unit tests for workflow routing service."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.core.plugins.routing import WorkflowExecutionService
from app.core.plugins.models import SourceWorkflowStep
from app.core.documents.models import Document, DocumentType
from app.core.plugins.base import BasePlugin, PluginMetadata


class MockPlugin(BasePlugin):
    """Mock plugin for testing."""

    def __init__(self, name: str, input_types: list[str], output_type: str | None = None):
        self._name = name
        self._input_types = input_types
        self._output_type = output_type

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name=self._name,
            version="1.0.0",
            display_name=f"{self._name.title()} Plugin",
            description=f"Mock {self._name} plugin",
            author="Test",
            input_types=self._input_types,
            output_type=self._output_type,
            priority=50,
            dependencies=[],
            max_concurrent_jobs=5,
            color="#000000",
            required_env_vars=[],
            settings_schema={},
        )

    @property
    def capabilities(self):
        """Return mock capabilities."""
        from app.core.plugins.base import PluginCapabilities
        return PluginCapabilities(
            has_routes=False,
            has_models=False,
            has_tasks=False,
            has_event_handlers=False,
            has_frontend=False,
            has_document_types=False,
        )

    async def setup(self, settings: dict) -> None:
        pass


@pytest.fixture
def mock_db():
    """Mock database session."""
    return AsyncMock()


@pytest.fixture
def mock_registry():
    """Mock plugin registry."""
    registry = MagicMock()

    # Define available plugins
    registry.plugins = {
        "audio_transcription": MockPlugin("audio_transcription", ["audio"], "transcription"),
        "sentiment_analysis": MockPlugin("sentiment_analysis", ["transcription"], "sentiment"),
        "summary_generator": MockPlugin("summary_generator", ["sentiment"], "summary"),
        "video_analysis": MockPlugin("video_analysis", ["video"], "analysis"),
    }

    registry.get = lambda name: registry.plugins.get(name)
    registry.get_handlers_for_document_type = lambda doc_type: [
        p for p in registry.plugins.values() if doc_type in p.metadata.input_types
    ]

    return registry


@pytest.fixture
def workflow_service(mock_db, mock_registry):
    """Create workflow execution service."""
    return WorkflowExecutionService(mock_db, mock_registry)


@pytest.mark.asyncio
async def test_get_workflow_for_source_simple(workflow_service, mock_db, mock_registry):
    """Test getting a simple workflow for a source."""
    source_id = uuid4()
    doc_type = "audio"

    # Create workflow steps
    steps = [
        SourceWorkflowStep(
            id=uuid4(),
            source_id=source_id,
            document_type=doc_type,
            sequence_number=1,
            plugin_name="audio_transcription",
            is_enabled=True,
            settings={},
        )
    ]

    # Mock database response
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = steps
    mock_db.execute = AsyncMock(return_value=mock_result)

    # Get workflow
    workflow = await workflow_service._get_workflow_for_source(source_id, doc_type)

    # Verify
    assert len(workflow) == 1
    assert workflow[0][0] == 1  # sequence_number
    assert workflow[0][1].metadata.name == "audio_transcription"
    assert workflow[0][2] == {}  # settings


@pytest.mark.asyncio
async def test_get_workflow_for_source_chain(workflow_service, mock_db, mock_registry):
    """Test getting a multi-step workflow (chain processing)."""
    source_id = uuid4()
    doc_type = "audio"

    # Create workflow steps: audio → transcription → sentiment → summary
    steps = [
        SourceWorkflowStep(
            id=uuid4(),
            source_id=source_id,
            document_type=doc_type,
            sequence_number=1,
            plugin_name="audio_transcription",
            is_enabled=True,
            settings={},
        ),
        SourceWorkflowStep(
            id=uuid4(),
            source_id=source_id,
            document_type=doc_type,
            sequence_number=2,
            plugin_name="sentiment_analysis",
            is_enabled=True,
            settings={},
        ),
        SourceWorkflowStep(
            id=uuid4(),
            source_id=source_id,
            document_type=doc_type,
            sequence_number=3,
            plugin_name="summary_generator",
            is_enabled=True,
            settings={},
        ),
    ]

    # Mock database response
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = steps
    mock_db.execute = AsyncMock(return_value=mock_result)

    # Get workflow
    workflow = await workflow_service._get_workflow_for_source(source_id, doc_type)

    # Verify all steps are included
    assert len(workflow) == 3
    assert workflow[0][1].metadata.name == "audio_transcription"
    assert workflow[1][1].metadata.name == "sentiment_analysis"
    assert workflow[2][1].metadata.name == "summary_generator"

    # Verify type compatibility chain
    assert "audio" in workflow[0][1].metadata.input_types
    assert workflow[0][1].metadata.output_type == "transcription"
    assert "transcription" in workflow[1][1].metadata.input_types
    assert workflow[1][1].metadata.output_type == "sentiment"
    assert "sentiment" in workflow[2][1].metadata.input_types


@pytest.mark.asyncio
async def test_get_workflow_validation_fails_incompatible_types(workflow_service, mock_db, mock_registry):
    """Test that workflow validation fails when types are incompatible."""
    source_id = uuid4()
    doc_type = "audio"

    # Create workflow with incompatible types: audio → video_analysis (wrong!)
    steps = [
        SourceWorkflowStep(
            id=uuid4(),
            source_id=source_id,
            document_type=doc_type,
            sequence_number=1,
            plugin_name="audio_transcription",
            is_enabled=True,
            settings={},
        ),
        SourceWorkflowStep(
            id=uuid4(),
            source_id=source_id,
            document_type=doc_type,
            sequence_number=2,
            plugin_name="video_analysis",  # Requires "video", but gets "transcription"
            is_enabled=True,
            settings={},
        ),
    ]

    # Mock database response
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = steps
    mock_db.execute = AsyncMock(return_value=mock_result)

    # Get workflow
    workflow = await workflow_service._get_workflow_for_source(source_id, doc_type)

    # Verify workflow is truncated (stops at incompatible step)
    assert len(workflow) == 1
    assert workflow[0][1].metadata.name == "audio_transcription"


@pytest.mark.asyncio
async def test_get_workflow_for_document_with_source(workflow_service, mock_db, mock_registry):
    """Test getting workflow for a document with source_id."""
    source_id = uuid4()

    # Create document with source
    doc_type = DocumentType(id=uuid4(), name="audio", display_name="Audio", registered_by="upload")
    document = Document(
        id=uuid4(),
        type_id=doc_type.id,
        owner_id=uuid4(),
        source_id=source_id,
        storage_plugin="upload",
        filepath="test.mp3",
        content_type="audio/mpeg",
        size_bytes=1024,
        checksum="abc123",
    )
    document.document_type = doc_type

    # Create workflow steps
    steps = [
        SourceWorkflowStep(
            id=uuid4(),
            source_id=source_id,
            document_type="audio",
            sequence_number=1,
            plugin_name="audio_transcription",
            is_enabled=True,
            settings={},
        )
    ]

    # Mock database response
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = steps
    mock_db.execute = AsyncMock(return_value=mock_result)

    # Get workflow
    workflow = await workflow_service.get_workflow_for_document(document)

    # Verify
    assert len(workflow) == 1
    assert workflow[0][1].metadata.name == "audio_transcription"


@pytest.mark.asyncio
async def test_get_workflow_for_document_without_source_uses_user_workflow(workflow_service, mock_db, mock_registry):
    """Test that documents without source_id fall back to user workflow."""
    # Create document WITHOUT source
    doc_type = DocumentType(id=uuid4(), name="audio", display_name="Audio", registered_by="upload")
    document = Document(
        id=uuid4(),
        type_id=doc_type.id,
        owner_id=uuid4(),
        source_id=None,  # No source!
        storage_plugin="upload",
        filepath="test.mp3",
        content_type="audio/mpeg",
        size_bytes=1024,
        checksum="abc123",
    )
    document.document_type = doc_type

    # Mock database response - no user workflow configured
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_db.execute = AsyncMock(return_value=mock_result)

    # Get workflow (falls back to user workflow, which is empty)
    workflow = await workflow_service.get_workflow_for_document(document)

    # When no source workflow and no user workflow, returns empty list
    assert len(workflow) == 0


@pytest.mark.asyncio
async def test_get_workflow_skips_missing_plugins(workflow_service, mock_db, mock_registry):
    """Test that workflow skips steps with missing plugins."""
    source_id = uuid4()
    doc_type = "audio"

    # Create workflow with a missing plugin
    steps = [
        SourceWorkflowStep(
            id=uuid4(),
            source_id=source_id,
            document_type=doc_type,
            sequence_number=1,
            plugin_name="missing_plugin",  # Doesn't exist!
            is_enabled=True,
            settings={},
        ),
        SourceWorkflowStep(
            id=uuid4(),
            source_id=source_id,
            document_type=doc_type,
            sequence_number=2,
            plugin_name="audio_transcription",
            is_enabled=True,
            settings={},
        ),
    ]

    # Mock database response
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = steps
    mock_db.execute = AsyncMock(return_value=mock_result)

    # Get workflow
    workflow = await workflow_service._get_workflow_for_source(source_id, doc_type)

    # Verify missing plugin was skipped, but valid one is included
    # Since the first step is missing, we skip it and continue with step 2
    # Step 2 (audio_transcription) expects "audio" which matches the original doc_type
    assert len(workflow) == 1
    assert workflow[0][1].metadata.name == "audio_transcription"


@pytest.mark.asyncio
async def test_get_workflow_empty_for_no_steps(workflow_service, mock_db, mock_registry):
    """Test that workflow is empty when no steps configured."""
    source_id = uuid4()
    doc_type = "audio"

    # Mock database response with no steps
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_db.execute = AsyncMock(return_value=mock_result)

    # Get workflow
    workflow = await workflow_service._get_workflow_for_source(source_id, doc_type)

    # Verify
    assert len(workflow) == 0
