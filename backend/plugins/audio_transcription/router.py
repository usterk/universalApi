"""Audio Transcription plugin router."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database.session import get_db
from app.core.auth.dependencies import CurrentActiveUser
from plugins.audio_transcription.models import Transcription, TranscriptionWord

router = APIRouter()


class WordResponse(BaseModel):
    word: str
    start_time: float
    end_time: float
    confidence: float | None

    class Config:
        from_attributes = True


class TranscriptionResponse(BaseModel):
    id: str
    document_id: str
    full_text: str
    language: str
    language_probability: float | None
    duration_seconds: float | None
    model_used: str
    processing_time_seconds: float | None
    word_count: int
    created_at: str

    class Config:
        from_attributes = True


class TranscriptionDetailResponse(TranscriptionResponse):
    words: list[WordResponse]


class TranscriptionListResponse(BaseModel):
    transcriptions: list[TranscriptionResponse]
    total: int
    page: int
    page_size: int


@router.get("/transcriptions", response_model=TranscriptionListResponse)
async def list_transcriptions(
    current_user: CurrentActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    language: str | None = None,
) -> TranscriptionListResponse:
    """List transcriptions."""
    query = select(Transcription)

    if language:
        query = query.where(Transcription.language == language)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Paginate
    query = (
        query.options(selectinload(Transcription.words))
        .order_by(Transcription.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    result = await db.execute(query)
    transcriptions = result.scalars().all()

    return TranscriptionListResponse(
        transcriptions=[
            TranscriptionResponse(
                id=str(t.id),
                document_id=str(t.document_id),
                full_text=t.full_text[:500] + "..." if len(t.full_text) > 500 else t.full_text,
                language=t.language,
                language_probability=t.language_probability,
                duration_seconds=t.duration_seconds,
                model_used=t.model_used,
                processing_time_seconds=t.processing_time_seconds,
                word_count=len(t.words),
                created_at=t.created_at.isoformat(),
            )
            for t in transcriptions
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/transcriptions/{transcription_id}", response_model=TranscriptionDetailResponse)
async def get_transcription(
    transcription_id: UUID,
    current_user: CurrentActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TranscriptionDetailResponse:
    """Get transcription with words."""
    result = await db.execute(
        select(Transcription)
        .options(selectinload(Transcription.words))
        .where(Transcription.id == transcription_id)
    )
    transcription = result.scalar_one_or_none()

    if transcription is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcription not found",
        )

    return TranscriptionDetailResponse(
        id=str(transcription.id),
        document_id=str(transcription.document_id),
        full_text=transcription.full_text,
        language=transcription.language,
        language_probability=transcription.language_probability,
        duration_seconds=transcription.duration_seconds,
        model_used=transcription.model_used,
        processing_time_seconds=transcription.processing_time_seconds,
        word_count=len(transcription.words),
        created_at=transcription.created_at.isoformat(),
        words=[
            WordResponse(
                word=w.word,
                start_time=w.start_time,
                end_time=w.end_time,
                confidence=w.confidence,
            )
            for w in transcription.words
        ],
    )


@router.get("/transcriptions/{transcription_id}/words", response_model=list[WordResponse])
async def get_transcription_words(
    transcription_id: UUID,
    current_user: CurrentActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    start_time: float | None = None,
    end_time: float | None = None,
) -> list[WordResponse]:
    """Get words for a transcription, optionally filtered by time range."""
    query = select(TranscriptionWord).where(
        TranscriptionWord.transcription_id == transcription_id
    )

    if start_time is not None:
        query = query.where(TranscriptionWord.start_time >= start_time)

    if end_time is not None:
        query = query.where(TranscriptionWord.end_time <= end_time)

    query = query.order_by(TranscriptionWord.start_time)

    result = await db.execute(query)
    words = result.scalars().all()

    return [
        WordResponse(
            word=w.word,
            start_time=w.start_time,
            end_time=w.end_time,
            confidence=w.confidence,
        )
        for w in words
    ]


@router.post("/transcriptions/{transcription_id}/regenerate")
async def regenerate_transcription(
    transcription_id: UUID,
    current_user: CurrentActiveUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """Regenerate transcription for a document."""
    result = await db.execute(
        select(Transcription).where(Transcription.id == transcription_id)
    )
    transcription = result.scalar_one_or_none()

    if transcription is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcription not found",
        )

    # Queue regeneration task
    from plugins.audio_transcription.tasks import transcribe_audio
    from app.core.queue.celery_app import celery_app

    task = celery_app.send_task(
        "audio_transcription.process",
        args=[str(transcription.document_id)],
        kwargs={"regenerate": True},
    )

    return {
        "status": "queued",
        "task_id": task.id,
        "document_id": str(transcription.document_id),
    }
