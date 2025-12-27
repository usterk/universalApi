"""Audio Transcription plugin models.

DEPRECATED: This module is no longer used.

Universal Document Pattern: Transcription data is now stored as child Documents
with properties containing the transcription text, language, and other metadata.

The old Transcription and TranscriptionWord tables have been migrated to Documents.
See migration: a1b2c3d4e5f6_migrate_transcriptions_to_documents.py

For reference, the old schema was:
- Transcription: id, document_id, full_text, language, duration_seconds, model_used, etc.
- TranscriptionWord: id, transcription_id, word, start_time, end_time, confidence
"""

# Models removed - data now stored in Document.properties
