"""Processing jobs API endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database.session import get_db
from app.core.auth.dependencies import CurrentActiveUser
from app.core.plugins.models import ProcessingJob, JobStatus
from app.core.events.bus import get_event_bus
from app.core.events.types import EventType, EventSeverity
from app.core.queue.celery_app import celery_app
from datetime import datetime

router = APIRouter()


class CancelJobRequest(BaseModel):
    """Request to cancel a job."""

    reason: str | None = None


class JobResponse(BaseModel):
    """Job status response."""

    id: str
    document_id: str
    plugin_name: str
    status: str
    progress: int
    progress_message: str | None
    error_message: str | None
    created_at: str
    started_at: str | None
    completed_at: str | None

    class Config:
        from_attributes = True


@router.post("/{job_id}/cancel", status_code=status.HTTP_200_OK)
async def cancel_job(
    job_id: UUID,
    request: CancelJobRequest,
    current_user: CurrentActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """
    Cancel a running or queued job.

    - Revokes Celery task
    - Updates job status to CANCELLED
    - Emits job.cancelled event
    """
    # Get job
    result = await db.execute(select(ProcessingJob).where(ProcessingJob.id == job_id))
    job = result.scalar_one_or_none()

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    # Check if job belongs to user's documents
    from app.core.documents.models import Document

    doc_result = await db.execute(
        select(Document).where(
            Document.id == job.document_id,
            Document.owner_id == current_user.id,
        )
    )
    if doc_result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to cancel this job",
        )

    # Check if already completed/cancelled
    if job.status in [
        JobStatus.COMPLETED.value,
        JobStatus.CANCELLED.value,
        JobStatus.FAILED.value,
    ]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel job with status: {job.status}",
        )

    # Revoke Celery task
    if job.task_id:
        celery_app.control.revoke(job.task_id, terminate=True)

    # Update job
    job.status = JobStatus.CANCELLED.value
    job.completed_at = datetime.utcnow()
    job.error_message = request.reason or "Cancelled by user"

    await db.commit()

    # Emit event
    event_bus = get_event_bus()
    await event_bus.emit(
        event_type=EventType.JOB_CANCELLED,
        source="api:jobs",
        payload={
            "job_id": str(job_id),
            "plugin_name": job.plugin_name,
            "document_id": str(job.document_id),
            "reason": request.reason or "user_request",
            "cancelled_by": str(current_user.id),
        },
        user_id=current_user.id,
        severity=EventSeverity.WARNING,
        persist=True,
    )

    return {
        "message": "Job cancelled successfully",
        "job_id": str(job_id),
        "status": job.status,
    }


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: UUID,
    current_user: CurrentActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> JobResponse:
    """Get job status."""
    result = await db.execute(select(ProcessingJob).where(ProcessingJob.id == job_id))
    job = result.scalar_one_or_none()

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    # Check ownership
    from app.core.documents.models import Document

    doc_result = await db.execute(
        select(Document).where(
            Document.id == job.document_id,
            Document.owner_id == current_user.id,
        )
    )
    if doc_result.scalar_one_or_none() is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this job",
        )

    return JobResponse(
        id=str(job.id),
        document_id=str(job.document_id),
        plugin_name=job.plugin_name,
        status=job.status,
        progress=job.progress,
        progress_message=job.progress_message,
        error_message=job.error_message,
        created_at=job.created_at.isoformat(),
        started_at=job.started_at.isoformat() if job.started_at else None,
        completed_at=job.completed_at.isoformat() if job.completed_at else None,
    )
