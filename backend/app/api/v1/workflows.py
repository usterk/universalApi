"""User default workflow configuration endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import CurrentActiveUser
from app.core.database.session import get_db
from app.core.plugins.models import UserWorkflowStep
from app.core.plugins.registry import PluginRegistry

# Reuse Pydantic models from sources
from app.api.v1.sources import (
    WorkflowResponse,
    WorkflowStepResponse,
    AvailablePluginForWorkflowResponse,
    AddWorkflowStepRequest,
    ReorderWorkflowRequest,
)

router = APIRouter()


@router.get("/{document_type}", response_model=WorkflowResponse)
async def get_user_workflow(
    document_type: str,
    current_user: CurrentActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> WorkflowResponse:
    """
    Get user's default workflow for document type.

    Example: GET /workflows/audio
    Returns: List of workflow steps for audio files uploaded by user.
    """
    # Query workflow steps
    result = await db.execute(
        select(UserWorkflowStep)
        .where(
            UserWorkflowStep.user_id == current_user.id,
            UserWorkflowStep.document_type == document_type
        )
        .order_by(UserWorkflowStep.sequence_number)
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

    return WorkflowResponse(document_type=document_type, steps=step_responses)


@router.get("/{document_type}/available-plugins", response_model=list[AvailablePluginForWorkflowResponse])
async def get_available_plugins_for_user_workflow(
    document_type: str,
    current_user: CurrentActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_step: int | None = None,
) -> list[AvailablePluginForWorkflowResponse]:
    """
    Get plugins that can be added to user workflow.

    Smart filtering based on type compatibility:
    - If current_step is None (or 0): Return plugins that accept document_type
    - If current_step > 0: Return plugins that accept previous step's output type
    """
    registry = PluginRegistry()

    # Determine expected input type (matches sources.py logic)
    expected_input_type = document_type
    if current_step is not None and current_step > 1:
        # Get previous step to find output_type
        result = await db.execute(
            select(UserWorkflowStep).where(
                UserWorkflowStep.user_id == current_user.id,
                UserWorkflowStep.document_type == document_type,
                UserWorkflowStep.sequence_number == current_step - 1
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


@router.post("/{document_type}/steps", response_model=WorkflowStepResponse, status_code=status.HTTP_201_CREATED)
async def add_user_workflow_step(
    document_type: str,
    data: AddWorkflowStepRequest,
    current_user: CurrentActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> WorkflowStepResponse:
    """
    Add step to user default workflow.

    Validates type compatibility:
    - First step must accept document_type
    - Subsequent steps must accept previous step's output type
    """
    registry = PluginRegistry()
    plugin = registry.get(data.plugin_name)

    if not plugin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Plugin {data.plugin_name} not found"
        )

    # Validate type compatibility
    if data.sequence_number == 1:
        # First step: must accept document type
        if document_type not in plugin.metadata.input_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Plugin {data.plugin_name} cannot process {document_type}. "
                       f"Accepts: {', '.join(plugin.metadata.input_types)}"
            )
    else:
        # Subsequent step: must accept previous step's output
        result = await db.execute(
            select(UserWorkflowStep)
            .where(
                UserWorkflowStep.user_id == current_user.id,
                UserWorkflowStep.document_type == document_type,
                UserWorkflowStep.sequence_number == data.sequence_number - 1
            )
        )
        previous_step = result.scalar_one_or_none()

        if not previous_step:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot add step {data.sequence_number}: previous step not found"
            )

        prev_plugin = registry.get(previous_step.plugin_name)
        if not prev_plugin:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Previous plugin {previous_step.plugin_name} not found"
            )

        expected_input = prev_plugin.metadata.output_type or document_type
        if expected_input not in plugin.metadata.input_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Type mismatch: {prev_plugin.metadata.display_name} outputs '{expected_input}', "
                       f"but {plugin.metadata.display_name} expects {', '.join(plugin.metadata.input_types)}"
            )

    # Create workflow step
    workflow_step = UserWorkflowStep(
        user_id=current_user.id,
        document_type=document_type,
        sequence_number=data.sequence_number,
        plugin_name=data.plugin_name,
        settings=data.settings,
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


@router.delete("/{document_type}/steps/{step_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_workflow_step(
    document_type: str,
    step_id: UUID,
    current_user: CurrentActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete step from user default workflow."""
    result = await db.execute(
        select(UserWorkflowStep).where(
            UserWorkflowStep.id == step_id,
            UserWorkflowStep.user_id == current_user.id,
            UserWorkflowStep.document_type == document_type
        )
    )
    step = result.scalar_one_or_none()

    if not step:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow step not found"
        )

    await db.delete(step)
    await db.commit()


@router.put("/{document_type}/reorder", response_model=WorkflowResponse)
async def reorder_user_workflow(
    document_type: str,
    data: ReorderWorkflowRequest,
    current_user: CurrentActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> WorkflowResponse:
    """
    Reorder user workflow steps.

    Validates entire workflow after reordering to ensure type compatibility.
    """
    # Update sequence numbers
    for step_update in data.steps:
        step_id = UUID(step_update["id"])
        new_sequence = step_update["sequence_number"]

        result = await db.execute(
            select(UserWorkflowStep).where(
                UserWorkflowStep.id == step_id,
                UserWorkflowStep.user_id == current_user.id,
                UserWorkflowStep.document_type == document_type
            )
        )
        step = result.scalar_one_or_none()

        if step:
            step.sequence_number = new_sequence

    await db.commit()

    # Validate the reordered workflow
    result = await db.execute(
        select(UserWorkflowStep)
        .where(
            UserWorkflowStep.user_id == current_user.id,
            UserWorkflowStep.document_type == document_type
        )
        .order_by(UserWorkflowStep.sequence_number)
    )
    steps = result.scalars().all()

    registry = PluginRegistry()
    expected_input_type = document_type

    for step in steps:
        plugin = registry.get(step.plugin_name)
        if not plugin:
            continue

        if expected_input_type not in plugin.metadata.input_types:
            # Rollback on validation error
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid workflow: Step {step.sequence_number} ({plugin.metadata.display_name}) "
                       f"expects {', '.join(plugin.metadata.input_types)}, "
                       f"but previous step outputs '{expected_input_type}'"
            )

        expected_input_type = plugin.metadata.output_type or document_type

    # Return updated workflow
    return await get_user_workflow(document_type, current_user, db)
