"""Audio Transcription Celery tasks."""

import time
from pathlib import Path
from uuid import UUID

from celery import shared_task
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.core.queue.base_task import PluginTask
from app.core.ai.openai import get_openai_provider
from plugins.audio_transcription.models import Transcription, TranscriptionWord


def get_sync_session() -> Session:
    """Get synchronous database session for Celery tasks."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    engine = create_engine(settings.database_url_sync)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


@shared_task(bind=True, base=PluginTask, name="audio_transcription.process")
def transcribe_audio(
    self,
    document_id: str,
    regenerate: bool = False,
) -> dict:
    """
    Transcribe an audio document.

    Args:
        document_id: UUID of the document to transcribe
        regenerate: If True, delete existing transcription first

    Returns:
        Result dict with transcription info
    """
    import asyncio

    # Run async code in sync context
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        result = loop.run_until_complete(
            _transcribe_audio_async(self, document_id, regenerate)
        )
        return result
    finally:
        loop.close()


async def _transcribe_audio_async(
    task: PluginTask,
    document_id: str,
    regenerate: bool,
) -> dict:
    """Async implementation of transcription."""
    from app.core.documents.models import Document

    start_time = time.time()
    doc_uuid = UUID(document_id)

    task.emit_started(document_id)
    task.update_progress(document_id, 5, "Loading document")

    with get_sync_session() as session:
        # Get document
        result = session.execute(select(Document).where(Document.id == doc_uuid))
        document = result.scalar_one_or_none()

        if document is None:
            raise ValueError(f"Document {document_id} not found")

        # Check if already transcribed
        if not regenerate:
            existing = session.execute(
                select(Transcription).where(Transcription.document_id == doc_uuid)
            )
            if existing.scalar_one_or_none():
                return {"status": "already_transcribed", "document_id": document_id}

        # Delete existing if regenerating
        if regenerate:
            session.execute(
                select(Transcription).where(Transcription.document_id == doc_uuid)
            )
            existing = session.execute(
                select(Transcription).where(Transcription.document_id == doc_uuid)
            ).scalar_one_or_none()
            if existing:
                session.delete(existing)
                session.commit()

        task.update_progress(document_id, 10, "Loading audio file")

        # Load audio file
        file_path = Path(settings.storage_local_path) / document.filepath
        if not file_path.exists():
            raise ValueError(f"Audio file not found: {file_path}")

        audio_data = file_path.read_bytes()
        filename = document.properties.get("original_filename", "audio.mp3")

        task.update_progress(document_id, 20, "Starting transcription")

        # Transcribe using OpenAI
        provider = get_openai_provider()
        result = await provider.transcribe(
            audio_data=audio_data,
            filename=filename,
        )

        task.update_progress(document_id, 80, "Saving transcription")

        # Calculate processing time
        processing_time = time.time() - start_time

        # Create transcription record
        transcription = Transcription(
            document_id=doc_uuid,
            full_text=result.text,
            language=result.language,
            language_probability=result.language_probability,
            duration_seconds=result.duration,
            model_used=result.model,
            processing_time_seconds=processing_time,
        )
        session.add(transcription)
        session.flush()

        # Add words
        for word in result.words:
            word_record = TranscriptionWord(
                transcription_id=transcription.id,
                word=word.word,
                start_time=word.start,
                end_time=word.end,
                confidence=word.confidence,
            )
            session.add(word_record)

        session.commit()

        task.update_progress(document_id, 100, "Complete")

        return {
            "status": "completed",
            "document_id": document_id,
            "transcription_id": str(transcription.id),
            "language": result.language,
            "word_count": len(result.words),
            "duration_seconds": result.duration,
            "processing_time_seconds": processing_time,
        }
