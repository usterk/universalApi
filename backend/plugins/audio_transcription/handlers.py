"""Audio Transcription event handlers."""

from app.core.events.types import Event
from app.core.queue.celery_app import celery_app


async def on_document_created(event: Event) -> None:
    """
    Handle document.created event.

    If the document is an audio file, queue it for transcription.
    """
    payload = event.payload
    document_type = payload.get("document_type")

    # Only process audio documents
    if document_type != "audio":
        return

    document_id = payload.get("document_id")
    if not document_id:
        return

    # Queue transcription task
    celery_app.send_task(
        "audio_transcription.process",
        args=[document_id],
        queue="transcription",
    )
