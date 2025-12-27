"""Audio Transcription plugin router.

DEPRECATED: This module is no longer used.

Universal Document Pattern: Transcription data is now accessed via the
/documents API. Transcriptions are child Documents with parent_id pointing
to the audio document.

To get transcriptions for an audio document:
- GET /documents/{audio_id}?include=children
- Or: GET /documents?parent_id={audio_id}

To get a specific transcription:
- GET /documents/{transcription_id}
- The properties field contains: full_text, language, duration_seconds, etc.

For regeneration, trigger via the workflow system or directly send a task.
"""

# Router removed - use /documents API instead
