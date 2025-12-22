"""Plugins management API endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.session import get_db
from app.core.auth.dependencies import CurrentSuperuser, CurrentActiveUser
from app.core.plugins.models import PluginConfig, PluginFilter, ProcessingJob, JobStatus
from app.core.plugins.registry import PluginRegistry

router = APIRouter()


class PluginResponse(BaseModel):
    name: str
    display_name: str
    version: str
    description: str
    is_enabled: bool
    priority: int
    max_concurrent_jobs: int
    input_types: list[str]
    output_type: str | None
    dependencies: list[str]
    color: str
    state: str

    class Config:
        from_attributes = True


class PluginSettingsUpdate(BaseModel):
    settings: dict


class PluginFilterCreate(BaseModel):
    filter_type: str
    operator: str
    value: str


class PluginFilterResponse(BaseModel):
    id: str
    plugin_name: str
    filter_type: str
    operator: str
    value: str
    created_at: str

    class Config:
        from_attributes = True


class JobResponse(BaseModel):
    id: str
    document_id: str
    plugin_name: str
    status: str
    progress: int
    progress_message: str | None
    result: dict | None
    error_message: str | None
    output_document_id: str | None
    started_at: str | None
    completed_at: str | None
    created_at: str

    class Config:
        from_attributes = True


def get_registry(request: Request) -> PluginRegistry:
    """Get plugin registry from app state."""
    return request.app.state.plugin_registry


# =============================================================================
# Jobs endpoints - MUST come before /{plugin_name} routes
# =============================================================================

@router.get("/jobs", response_model=list[JobResponse])
async def list_jobs(
    current_user: CurrentActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    plugin_name: str | None = None,
    status_filter: str | None = None,
    limit: int = 50,
) -> list[JobResponse]:
    """List processing jobs."""
    query = select(ProcessingJob).order_by(ProcessingJob.created_at.desc()).limit(limit)

    if plugin_name:
        query = query.where(ProcessingJob.plugin_name == plugin_name)

    if status_filter:
        query = query.where(ProcessingJob.status == status_filter)

    result = await db.execute(query)
    jobs = result.scalars().all()

    return [
        JobResponse(
            id=str(j.id),
            document_id=str(j.document_id),
            plugin_name=j.plugin_name,
            status=j.status,
            progress=j.progress,
            progress_message=j.progress_message,
            result=j.result,
            error_message=j.error_message,
            output_document_id=str(j.output_document_id) if j.output_document_id else None,
            started_at=j.started_at.isoformat() if j.started_at else None,
            completed_at=j.completed_at.isoformat() if j.completed_at else None,
            created_at=j.created_at.isoformat(),
        )
        for j in jobs
    ]


@router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: UUID,
    current_user: CurrentActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> JobResponse:
    """Get job details."""
    result = await db.execute(select(ProcessingJob).where(ProcessingJob.id == job_id))
    job = result.scalar_one_or_none()

    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    return JobResponse(
        id=str(job.id),
        document_id=str(job.document_id),
        plugin_name=job.plugin_name,
        status=job.status,
        progress=job.progress,
        progress_message=job.progress_message,
        result=job.result,
        error_message=job.error_message,
        output_document_id=str(job.output_document_id) if job.output_document_id else None,
        started_at=job.started_at.isoformat() if job.started_at else None,
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
        created_at=job.created_at.isoformat(),
    )


@router.post("/jobs/{job_id}/cancel", status_code=status.HTTP_200_OK)
async def cancel_job(
    job_id: UUID,
    current_user: CurrentActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Cancel a pending or running job."""
    result = await db.execute(select(ProcessingJob).where(ProcessingJob.id == job_id))
    job = result.scalar_one_or_none()

    if job is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")

    if job.status not in [JobStatus.PENDING.value, JobStatus.QUEUED.value, JobStatus.RUNNING.value]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel job with status {job.status}",
        )

    job.status = JobStatus.CANCELLED.value
    await db.commit()

    # TODO: Also revoke Celery task if running

    return {"status": "cancelled", "job_id": str(job_id)}


# =============================================================================
# Plugin management endpoints
# =============================================================================

@router.get("", response_model=list[PluginResponse])
async def list_plugins(
    current_user: CurrentActiveUser,
    registry: Annotated[PluginRegistry, Depends(get_registry)],
) -> list[PluginResponse]:
    """List all plugins."""
    plugins = []

    for plugin in registry.plugins.values():
        meta = plugin.metadata
        plugins.append(
            PluginResponse(
                name=meta.name,
                display_name=meta.display_name,
                version=meta.version,
                description=meta.description,
                is_enabled=plugin.state.value == "active",
                priority=meta.priority,
                max_concurrent_jobs=meta.max_concurrent_jobs,
                input_types=meta.input_types,
                output_type=meta.output_type,
                dependencies=meta.dependencies,
                color=meta.color,
                state=plugin.state.value,
            )
        )

    return sorted(plugins, key=lambda p: p.priority)


@router.get("/{plugin_name}", response_model=PluginResponse)
async def get_plugin(
    plugin_name: str,
    current_user: CurrentActiveUser,
    registry: Annotated[PluginRegistry, Depends(get_registry)],
) -> PluginResponse:
    """Get plugin details."""
    plugin = registry.get(plugin_name)

    if plugin is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plugin not found")

    meta = plugin.metadata
    return PluginResponse(
        name=meta.name,
        display_name=meta.display_name,
        version=meta.version,
        description=meta.description,
        is_enabled=plugin.state.value == "active",
        priority=meta.priority,
        max_concurrent_jobs=meta.max_concurrent_jobs,
        input_types=meta.input_types,
        output_type=meta.output_type,
        dependencies=meta.dependencies,
        color=meta.color,
        state=plugin.state.value,
    )


@router.post("/{plugin_name}/enable", response_model=PluginResponse)
async def enable_plugin(
    plugin_name: str,
    current_user: CurrentSuperuser,
    registry: Annotated[PluginRegistry, Depends(get_registry)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PluginResponse:
    """Enable a plugin."""
    plugin = registry.get(plugin_name)

    if plugin is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plugin not found")

    # Update config in DB
    result = await db.execute(
        select(PluginConfig).where(PluginConfig.plugin_name == plugin_name)
    )
    config = result.scalar_one_or_none()

    if config:
        config.is_enabled = True
    else:
        config = PluginConfig(
            plugin_name=plugin_name,
            is_enabled=True,
            display_name=plugin.metadata.display_name,
            version=plugin.metadata.version,
            priority=plugin.metadata.priority,
            max_concurrent_jobs=plugin.metadata.max_concurrent_jobs,
        )
        db.add(config)

    await db.commit()

    # TODO: Actually enable the plugin at runtime

    meta = plugin.metadata
    return PluginResponse(
        name=meta.name,
        display_name=meta.display_name,
        version=meta.version,
        description=meta.description,
        is_enabled=True,
        priority=meta.priority,
        max_concurrent_jobs=meta.max_concurrent_jobs,
        input_types=meta.input_types,
        output_type=meta.output_type,
        dependencies=meta.dependencies,
        color=meta.color,
        state=plugin.state.value,
    )


@router.post("/{plugin_name}/disable", response_model=PluginResponse)
async def disable_plugin(
    plugin_name: str,
    current_user: CurrentSuperuser,
    registry: Annotated[PluginRegistry, Depends(get_registry)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PluginResponse:
    """Disable a plugin."""
    plugin = registry.get(plugin_name)

    if plugin is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plugin not found")

    # Update config in DB
    result = await db.execute(
        select(PluginConfig).where(PluginConfig.plugin_name == plugin_name)
    )
    config = result.scalar_one_or_none()

    if config:
        config.is_enabled = False
        await db.commit()

    meta = plugin.metadata
    return PluginResponse(
        name=meta.name,
        display_name=meta.display_name,
        version=meta.version,
        description=meta.description,
        is_enabled=False,
        priority=meta.priority,
        max_concurrent_jobs=meta.max_concurrent_jobs,
        input_types=meta.input_types,
        output_type=meta.output_type,
        dependencies=meta.dependencies,
        color=meta.color,
        state=plugin.state.value,
    )


@router.put("/{plugin_name}/settings")
async def update_plugin_settings(
    plugin_name: str,
    data: PluginSettingsUpdate,
    current_user: CurrentSuperuser,
    registry: Annotated[PluginRegistry, Depends(get_registry)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Update plugin settings."""
    plugin = registry.get(plugin_name)

    if plugin is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plugin not found")

    # Update config in DB
    result = await db.execute(
        select(PluginConfig).where(PluginConfig.plugin_name == plugin_name)
    )
    config = result.scalar_one_or_none()

    if config:
        config.settings = data.settings
    else:
        config = PluginConfig(
            plugin_name=plugin_name,
            settings=data.settings,
            display_name=plugin.metadata.display_name,
            version=plugin.metadata.version,
        )
        db.add(config)

    await db.commit()

    return {"status": "ok", "settings": data.settings}


@router.get("/{plugin_name}/filters", response_model=list[PluginFilterResponse])
async def list_plugin_filters(
    plugin_name: str,
    current_user: CurrentActiveUser,
    registry: Annotated[PluginRegistry, Depends(get_registry)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> list[PluginFilterResponse]:
    """List filters for a plugin."""
    plugin = registry.get(plugin_name)

    if plugin is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plugin not found")

    result = await db.execute(
        select(PluginFilter).where(PluginFilter.plugin_name == plugin_name)
    )
    filters = result.scalars().all()

    return [
        PluginFilterResponse(
            id=str(f.id),
            plugin_name=f.plugin_name,
            filter_type=f.filter_type,
            operator=f.operator,
            value=f.value,
            created_at=f.created_at.isoformat(),
        )
        for f in filters
    ]


@router.post(
    "/{plugin_name}/filters",
    response_model=PluginFilterResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_plugin_filter(
    plugin_name: str,
    data: PluginFilterCreate,
    current_user: CurrentSuperuser,
    registry: Annotated[PluginRegistry, Depends(get_registry)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PluginFilterResponse:
    """Create a filter for a plugin."""
    plugin = registry.get(plugin_name)

    if plugin is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plugin not found")

    filter_obj = PluginFilter(
        plugin_name=plugin_name,
        filter_type=data.filter_type,
        operator=data.operator,
        value=data.value,
    )

    db.add(filter_obj)
    await db.commit()
    await db.refresh(filter_obj)

    return PluginFilterResponse(
        id=str(filter_obj.id),
        plugin_name=filter_obj.plugin_name,
        filter_type=filter_obj.filter_type,
        operator=filter_obj.operator,
        value=filter_obj.value,
        created_at=filter_obj.created_at.isoformat(),
    )


@router.delete("/{plugin_name}/filters/{filter_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plugin_filter(
    plugin_name: str,
    filter_id: UUID,
    current_user: CurrentSuperuser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    """Delete a plugin filter."""
    result = await db.execute(
        select(PluginFilter).where(
            PluginFilter.id == filter_id, PluginFilter.plugin_name == plugin_name
        )
    )
    filter_obj = result.scalar_one_or_none()

    if filter_obj is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Filter not found")

    await db.delete(filter_obj)
    await db.commit()
