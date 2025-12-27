"""Audio Transcription with Words Celery tasks.

Universal Document Pattern: Creates child Document with transcription data including words[].
"""

import hashlib
import json
import time
from datetime import datetime
from pathlib import Path
from uuid import UUID, uuid4

from celery import shared_task
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.core.queue.base_task import PluginTask
from app.core.ai.openai import get_openai_provider


def get_sync_session() -> Session:
    """Get synchronous database session for Celery tasks."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    # Import all models to register them with SQLAlchemy
    from app.core.users.models import User  # noqa: F401
    from app.core.documents.models import Document, DocumentType  # noqa: F401
    from app.core.sources.models import Source  # noqa: F401

    engine = create_engine(settings.database_url_sync)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


@shared_task(bind=True, base=PluginTask, name="audio_transcription_words.process")
def transcribe_audio_words(
    self,
    document_id: str,
    regenerate: bool = False,
) -> dict:
    """
    Transcribe an audio document with word-level timestamps.

    Args:
        document_id: UUID of the document to transcribe
        regenerate: If True, delete existing transcription first

    Returns:
        Result dict with transcription info including word count
    """
    import asyncio

    # Run async code in sync context
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        result = loop.run_until_complete(
            _transcribe_audio_words_async(self, document_id, regenerate)
        )
        return result
    finally:
        loop.close()


async def _transcribe_audio_words_async(
    task: PluginTask,
    document_id: str,
    regenerate: bool,
) -> dict:
    """
    Async implementation of transcription with word-level timestamps.

    Universal Document Pattern: Creates child Document with transcription data.
    This plugin creates transcription WITH word-level timestamps in properties.words[].
    """
    from app.core.documents.models import Document, DocumentType

    start_time = time.time()
    doc_uuid = UUID(document_id)

    task.emit_started(job_id=document_id, document_id=document_id)
    task.update_progress(document_id, 5, "Loading document")

    with get_sync_session() as session:
        # Get parent document
        result = session.execute(select(Document).where(Document.id == doc_uuid))
        parent_doc = result.scalar_one_or_none()

        if parent_doc is None:
            raise ValueError(f"Document {document_id} not found")

        # Get transcription_words document type
        type_result = session.execute(
            select(DocumentType).where(DocumentType.name == "transcription_words")
        )
        transcription_type = type_result.scalar_one_or_none()

        if transcription_type is None:
            raise ValueError("Transcription words document type not found")

        # Check if already transcribed (look for child transcription documents)
        if not regenerate:
            existing = session.execute(
                select(Document).where(
                    Document.parent_id == doc_uuid,
                    Document.type_id == transcription_type.id,
                )
            )
            if existing.scalar_one_or_none():
                return {"status": "already_transcribed", "document_id": document_id}

        # Delete existing transcription if regenerating
        if regenerate:
            existing_docs = session.execute(
                select(Document).where(
                    Document.parent_id == doc_uuid,
                    Document.type_id == transcription_type.id,
                )
            ).scalars().all()
            for doc in existing_docs:
                session.delete(doc)
            if existing_docs:
                session.commit()

        task.update_progress(document_id, 10, "Loading audio file")

        # Load audio file
        file_path = Path(settings.storage_local_path) / parent_doc.filepath
        if not file_path.exists():
            raise ValueError(f"Audio file not found: {file_path}")

        audio_data = file_path.read_bytes()
        filename = parent_doc.properties.get("original_filename", "audio.mp3")

        task.update_progress(document_id, 20, "Starting transcription")

        # Transcribe using OpenAI
        provider = get_openai_provider()
        transcription_result = await provider.transcribe(
            audio_data=audio_data,
            filename=filename,
        )

        task.update_progress(document_id, 80, "Saving transcription with words")

        # Calculate processing time
        processing_time = time.time() - start_time

        # Prepare words array
        words = [
            {
                "word": word.word,
                "start": word.start,
                "end": word.end,
                "confidence": word.confidence,
            }
            for word in transcription_result.words
        ]

        # Prepare properties for child document (WITH words[])
        properties = {
            "full_text": transcription_result.text,
            "language": transcription_result.language,
            "language_probability": transcription_result.language_probability,
            "duration_seconds": transcription_result.duration,
            "model_used": transcription_result.model,
            "processing_time_seconds": processing_time,
            "original_filename": filename,
            "word_count": len(words),
            "words": words,
        }

        # Create JSON content for storage
        json_content = json.dumps(properties, ensure_ascii=False, indent=2)
        json_bytes = json_content.encode("utf-8")
        checksum = hashlib.sha256(json_bytes).hexdigest()

        # Generate filepath for the transcription document
        now = datetime.utcnow()
        child_id = uuid4()
        filepath = f"{now.year}/{now.month:02d}/{now.day:02d}/{child_id}.json"

        # Create child Document with transcription data including words
        child_doc = Document(
            id=child_id,
            type_id=transcription_type.id,
            parent_id=parent_doc.id,
            owner_id=parent_doc.owner_id,
            source_id=parent_doc.source_id,
            storage_plugin="audio_transcription_words",
            filepath=filepath,
            content_type="application/json",
            size_bytes=len(json_bytes),
            checksum=checksum,
            properties=properties,
        )
        session.add(child_doc)
        session.commit()

        task.update_progress(document_id, 100, "Complete")

        return {
            "status": "completed",
            "document_id": document_id,
            "child_document_id": str(child_doc.id),
            "language": transcription_result.language,
            "word_count": len(words),
            "duration_seconds": transcription_result.duration,
            "processing_time_seconds": processing_time,
        }
