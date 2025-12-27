"""Sources API endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.session import get_db
from app.core.auth.dependencies import CurrentActiveUser
from app.core.auth.api_keys import generate_api_key
from app.core.sources.models import Source
from app.core.plugins.models import SourceWorkflowStep, UserWorkflowStep
from app.core.plugins.registry import PluginRegistry

router = APIRouter()


class SourceCreate(BaseModel):
    name: str
    description: str | None = None
    properties: dict | None = None


class SourceResponse(BaseModel):
    id: str
    name: str
    description: str | None
    api_key_prefix: str
    is_active: bool
    properties: dict
    created_at: str

    class Config:
        from_attributes = True


class SourceWithKeyResponse(SourceResponse):
    """Response when creating source - includes full API key (shown once)."""

    api_key: str
    workflows_imported: int = 0  # Number of workflow steps imported from user defaults


class SourceUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    properties: dict | None = None
    is_active: bool | None = None


class SourceListResponse(BaseModel):
    """Paginated sources list response."""

    items: list[SourceResponse]
    total: int
    page: int
    page_size: int


@router.get("", response_model=SourceListResponse)
async def list_sources(
    current_user: CurrentActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> SourceListResponse:
    """List all sources for current user (paginated)."""
    # Count total
    count_result = await db.execute(
        select(func.count()).select_from(Source).where(Source.owner_id == current_user.id)
    )
    total = count_result.scalar_one()

    # Get paginated results
    offset = (page - 1) * page_size
    result = await db.execute(
        select(Source)
        .where(Source.owner_id == current_user.id)
        .order_by(Source.created_at.desc())
        .limit(page_size)
        .offset(offset)
    )
    sources = result.scalars().all()

    return SourceListResponse(
        items=[
            SourceResponse(
                id=str(s.id),
                name=s.name,
                description=s.description,
                api_key_prefix=s.api_key_prefix,
                is_active=s.is_active,
                properties=s.properties or {},
                created_at=s.created_at.isoformat(),
            )
            for s in sources
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=SourceWithKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_source(
    data: SourceCreate,
    current_user: CurrentActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SourceWithKeyResponse:
    """Create a new source with API key and import user default workflows."""
    # Generate API key
    full_key, key_hash, key_prefix = generate_api_key()

    source = Source(
        owner_id=current_user.id,
        name=data.name,
        description=data.description,
        api_key_hash=key_hash,
        api_key_prefix=key_prefix,
        properties=data.properties or {},
    )

    db.add(source)
    await db.commit()
    await db.refresh(source)

    # Import user default workflows to this source
    workflows_imported = await import_user_workflows_to_source(db, current_user.id, source.id)

    return SourceWithKeyResponse(
        id=str(source.id),
        name=source.name,
        description=source.description,
        api_key_prefix=source.api_key_prefix,
        api_key=full_key,  # Only shown once!
        is_active=source.is_active,
        properties=source.properties or {},
        created_at=source.created_at.isoformat(),
        workflows_imported=workflows_imported,
    )


@router.get("/{source_id}", response_model=SourceResponse)
async def get_source(
    source_id: UUID,
    current_user: CurrentActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SourceResponse:
    """Get source by ID."""
    result = await db.execute(
        select(Source).where(Source.id == source_id, Source.owner_id == current_user.id)
    )
    source = result.scalar_one_or_none()

    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")

    return SourceResponse(
        id=str(source.id),
        name=source.name,
        description=source.description,
        api_key_prefix=source.api_key_prefix,
        is_active=source.is_active,
        properties=source.properties or {},
        created_at=source.created_at.isoformat(),
    )


@router.patch("/{source_id}", response_model=SourceResponse)
async def update_source(
    source_id: UUID,
    data: SourceUpdate,
    current_user: CurrentActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SourceResponse:
    """Update source."""
    result = await db.execute(
        select(Source).where(Source.id == source_id, Source.owner_id == current_user.id)
    )
    source = result.scalar_one_or_none()

    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")

    if data.name is not None:
        source.name = data.name
    if data.description is not None:
        source.description = data.description
    if data.properties is not None:
        source.properties = data.properties
    if data.is_active is not None:
        source.is_active = data.is_active

    await db.commit()
    await db.refresh(source)

    return SourceResponse(
        id=str(source.id),
        name=source.name,
        description=source.description,
        api_key_prefix=source.api_key_prefix,
        is_active=source.is_active,
        properties=source.properties or {},
        created_at=source.created_at.isoformat(),
    )


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_source(
    source_id: UUID,
    current_user: CurrentActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete source."""
    result = await db.execute(
        select(Source).where(Source.id == source_id, Source.owner_id == current_user.id)
    )
    source = result.scalar_one_or_none()

    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")

    await db.delete(source)
    await db.commit()


@router.post("/{source_id}/regenerate-key", response_model=SourceWithKeyResponse)
async def regenerate_api_key(
    source_id: UUID,
    current_user: CurrentActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SourceWithKeyResponse:
    """Regenerate API key for source."""
    result = await db.execute(
        select(Source).where(Source.id == source_id, Source.owner_id == current_user.id)
    )
    source = result.scalar_one_or_none()

    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")

    # Generate new key
    full_key, key_hash, key_prefix = generate_api_key()
    source.api_key_hash = key_hash
    source.api_key_prefix = key_prefix

    await db.commit()
    await db.refresh(source)

    return SourceWithKeyResponse(
        id=str(source.id),
        name=source.name,
        description=source.description,
        api_key_prefix=source.api_key_prefix,
        api_key=full_key,
        is_active=source.is_active,
        properties=source.properties or {},
        created_at=source.created_at.isoformat(),
    )


# === HELPER FUNCTIONS ===


async def import_user_workflows_to_source(
    db: AsyncSession,
    user_id: UUID,
    source_id: UUID
) -> int:
    """
    Copy all user default workflows to new source.
    Returns number of steps imported.

    Called automatically when creating a source to initialize
    workflows from user defaults.
    """
    # Query all user workflow steps
    result = await db.execute(
        select(UserWorkflowStep)
        .where(UserWorkflowStep.user_id == user_id)
        .order_by(UserWorkflowStep.document_type, UserWorkflowStep.sequence_number)
    )
    user_steps = result.scalars().all()

    # Copy to source workflows
    for user_step in user_steps:
        source_step = SourceWorkflowStep(
            source_id=source_id,
            document_type=user_step.document_type,
            sequence_number=user_step.sequence_number,
            plugin_name=user_step.plugin_name,
            is_enabled=user_step.is_enabled,
            settings=user_step.settings.copy() if user_step.settings else {},
        )
        db.add(source_step)

    await db.commit()
    return len(user_steps)


# === WORKFLOW MANAGEMENT ===


class WorkflowStepResponse(BaseModel):
    """Single workflow step response."""

    id: str
    sequence_number: int
    plugin_name: str
    display_name: str
    input_types: list[str]
    output_type: str | None
    color: str
    settings: dict
    is_enabled: bool


class WorkflowResponse(BaseModel):
    """Complete workflow for a document type."""

    document_type: str
    steps: list[WorkflowStepResponse]


class AvailablePluginForWorkflowResponse(BaseModel):
    """Plugin available to add to workflow."""

    name: str
    display_name: str
    description: str
    input_types: list[str]
    output_type: str | None
    color: str


class AddWorkflowStepRequest(BaseModel):
    """Request to add a step to workflow."""

    plugin_name: str
    sequence_number: int
    settings: dict = {}


class ReorderWorkflowRequest(BaseModel):
    """Request to reorder workflow steps."""

    steps: list[dict]  # [{"id": "uuid", "sequence_number": 1}, ...]


@router.get("/{source_id}/workflows/{document_type}", response_model=WorkflowResponse)
async def get_workflow(
    source_id: UUID,
    document_type: str,
    current_user: CurrentActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> WorkflowResponse:
    """
    Pobierz workflow dla danego typu dokumentu.

    Przykład: GET /sources/123/workflows/audio
    Zwraca: Lista kroków workflow dla plików audio z tego source.
    """
    # Verify ownership
    result = await db.execute(
        select(Source).where(Source.id == source_id, Source.owner_id == current_user.id)
    )
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")

    # Query workflow steps
    result = await db.execute(
        select(SourceWorkflowStep)
        .where(
            SourceWorkflowStep.source_id == source_id,
            SourceWorkflowStep.document_type == document_type
        )
        .order_by(SourceWorkflowStep.sequence_number)
    )
    steps = result.scalars().all()

    # Get plugin registry to fetch metadata
    registry = PluginRegistry()

    step_responses = []
    for step in steps:
        plugin = registry.get(step.plugin_name)
        if plugin:
            step_responses.append(
                WorkflowStepResponse(
                    id=str(step.id),
                    sequence_number=step.sequence_number,
                    plugin_name=step.plugin_name,
                    display_name=plugin.metadata.display_name,
                    input_types=plugin.metadata.input_types,
                    output_type=plugin.metadata.output_type,
                    color=plugin.metadata.color,
                    settings=step.settings or {},
                    is_enabled=step.is_enabled,
                )
            )

    return WorkflowResponse(
        document_type=document_type,
        steps=step_responses,
    )


@router.get("/{source_id}/workflows/{document_type}/available-plugins")
async def get_available_plugins_for_workflow(
    source_id: UUID,
    document_type: str,
    current_user: CurrentActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_step: int | None = None,
) -> list[AvailablePluginForWorkflowResponse]:
    """
    Lista pluginów które można dodać do workflow.

    WAŻNE: Waliduje kompatybilność typów!
    - Jeśli current_step=None → pluginy które obsługują document_type
    - Jeśli current_step=2 → pluginy które obsługują output kroku poprzedniego
    """
    # Verify ownership
    result = await db.execute(
        select(Source).where(Source.id == source_id, Source.owner_id == current_user.id)
    )
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")

    registry = PluginRegistry()

    # Determine expected input type
    expected_input_type = document_type
    if current_step is not None and current_step > 1:
        # Get previous step to find output_type
        result = await db.execute(
            select(SourceWorkflowStep).where(
                SourceWorkflowStep.source_id == source_id,
                SourceWorkflowStep.document_type == document_type,
                SourceWorkflowStep.sequence_number == current_step - 1
            )
        )
        prev_step = result.scalar_one_or_none()
        if prev_step:
            prev_plugin = registry.get(prev_step.plugin_name)
            if prev_plugin and prev_plugin.metadata.output_type:
                expected_input_type = prev_plugin.metadata.output_type

    # Get all active plugins
    active_plugins = registry.get_active_plugins()

    # Filter: only plugins that accept expected_input_type
    compatible = []
    for plugin in active_plugins:
        if expected_input_type in plugin.metadata.input_types:
            compatible.append(
                AvailablePluginForWorkflowResponse(
                    name=plugin.metadata.name,
                    display_name=plugin.metadata.display_name,
                    description=plugin.metadata.description,
                    input_types=plugin.metadata.input_types,
                    output_type=plugin.metadata.output_type,
                    color=plugin.metadata.color,
                )
            )

    return compatible


@router.post("/{source_id}/workflows/{document_type}/steps", status_code=status.HTTP_201_CREATED)
async def add_workflow_step(
    source_id: UUID,
    document_type: str,
    data: AddWorkflowStepRequest,
    current_user: CurrentActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> WorkflowStepResponse:
    """
    Dodaj krok do workflow.

    WALIDUJE KOMPATYBILNOŚĆ: plugin musi obsługiwać typ poprzedniego kroku.
    """
    # Verify ownership
    result = await db.execute(
        select(Source).where(Source.id == source_id, Source.owner_id == current_user.id)
    )
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")

    # Validate plugin exists
    registry = PluginRegistry()
    plugin = registry.get(data.plugin_name)
    if not plugin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Plugin {data.plugin_name} not found"
        )

    # Validate compatibility with previous step
    if data.sequence_number > 1:
        result = await db.execute(
            select(SourceWorkflowStep).where(
                SourceWorkflowStep.source_id == source_id,
                SourceWorkflowStep.document_type == document_type,
                SourceWorkflowStep.sequence_number == data.sequence_number - 1
            )
        )
        prev_step = result.scalar_one_or_none()
        if prev_step:
            prev_plugin = registry.get(prev_step.plugin_name)
            if prev_plugin and prev_plugin.metadata.output_type:
                if prev_plugin.metadata.output_type not in plugin.metadata.input_types:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Plugin {plugin.name} cannot process output of previous step "
                               f"(expects {plugin.metadata.input_types}, got {prev_plugin.metadata.output_type})"
                    )
    else:
        # First step must accept document_type
        if document_type not in plugin.metadata.input_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Plugin {plugin.name} cannot process {document_type} documents"
            )

    # Create workflow step
    workflow_step = SourceWorkflowStep(
        source_id=source_id,
        document_type=document_type,
        sequence_number=data.sequence_number,
        plugin_name=data.plugin_name,
        settings=data.settings,
        is_enabled=True,
    )

    db.add(workflow_step)
    await db.commit()
    await db.refresh(workflow_step)

    return WorkflowStepResponse(
        id=str(workflow_step.id),
        sequence_number=workflow_step.sequence_number,
        plugin_name=workflow_step.plugin_name,
        display_name=plugin.metadata.display_name,
        input_types=plugin.metadata.input_types,
        output_type=plugin.metadata.output_type,
        color=plugin.metadata.color,
        settings=workflow_step.settings or {},
        is_enabled=workflow_step.is_enabled,
    )


@router.delete("/{source_id}/workflows/{document_type}/steps/{step_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workflow_step(
    source_id: UUID,
    document_type: str,
    step_id: UUID,
    current_user: CurrentActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Usuń krok z workflow."""
    # Verify ownership
    result = await db.execute(
        select(Source).where(Source.id == source_id, Source.owner_id == current_user.id)
    )
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")

    # Delete step
    result = await db.execute(
        select(SourceWorkflowStep).where(
            SourceWorkflowStep.id == step_id,
            SourceWorkflowStep.source_id == source_id,
            SourceWorkflowStep.document_type == document_type
        )
    )
    step = result.scalar_one_or_none()
    if not step:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow step not found")

    await db.delete(step)
    await db.commit()


@router.put("/{source_id}/workflows/{document_type}/reorder")
async def reorder_workflow(
    source_id: UUID,
    document_type: str,
    data: ReorderWorkflowRequest,
    current_user: CurrentActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> WorkflowResponse:
    """
    Zmień kolejność kroków w workflow (drag & drop).

    WALIDUJE: nowa kolejność musi być kompatybilna (typy się zgadzają).
    """
    # Verify ownership
    result = await db.execute(
        select(Source).where(Source.id == source_id, Source.owner_id == current_user.id)
    )
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")

    registry = PluginRegistry()

    # Update sequence numbers
    for step_data in data.steps:
        step_id = UUID(step_data["id"])
        new_sequence = step_data["sequence_number"]

        result = await db.execute(
            select(SourceWorkflowStep).where(SourceWorkflowStep.id == step_id)
        )
        step = result.scalar_one_or_none()
        if step:
            step.sequence_number = new_sequence

    await db.commit()

    # Validate new workflow (similar to get_workflow but with validation)
    result = await db.execute(
        select(SourceWorkflowStep)
        .where(
            SourceWorkflowStep.source_id == source_id,
            SourceWorkflowStep.document_type == document_type
        )
        .order_by(SourceWorkflowStep.sequence_number)
    )
    steps = result.scalars().all()

    # Validate type compatibility
    expected_input_type = document_type
    for step in steps:
        plugin = registry.get(step.plugin_name)
        if not plugin:
            continue

        if expected_input_type not in plugin.metadata.input_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid workflow order: Step {step.sequence_number} ({plugin.name}) "
                       f"cannot process {expected_input_type}"
            )

        expected_input_type = plugin.metadata.output_type or document_type

    # Return updated workflow
    step_responses = []
    for step in steps:
        plugin = registry.get(step.plugin_name)
        if plugin:
            step_responses.append(
                WorkflowStepResponse(
                    id=str(step.id),
                    sequence_number=step.sequence_number,
                    plugin_name=step.plugin_name,
                    display_name=plugin.metadata.display_name,
                    input_types=plugin.metadata.input_types,
                    output_type=plugin.metadata.output_type,
                    color=plugin.metadata.color,
                    settings=step.settings or {},
                    is_enabled=step.is_enabled,
                )
            )

    return WorkflowResponse(
        document_type=document_type,
        steps=step_responses,
    )
