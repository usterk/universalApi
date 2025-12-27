"""Audio Transcription with Speaker Diarization event handlers."""

from app.core.events.types import Event
from app.core.queue.celery_app import celery_app
from app.core.plugins.handler_wrapper import create_routing_aware_handler


async def _handle_document_created(event: Event) -> None:
    """
    Internal handler for document.created event.

    Queues audio documents for transcription with speaker diarization.
    Called only after workflow routing validation passes.
    """
    payload = event.payload
    document_type = payload.get("document_type")

    # Only process audio documents
    if document_type != "audio":
        return

    document_id = payload.get("document_id")
    if not document_id:
        return

    # Queue transcription task with diarization
    celery_app.send_task(
        "audio_transcription_diarize.process",
        args=[document_id],
        queue="transcription",
    )


# Export wrapped handler that respects workflow routing
on_document_created = create_routing_aware_handler(
    "audio_transcription_diarize",
    _handle_document_created
)
