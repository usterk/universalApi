# Plugin: Audio Transcription

Transcribes audio files using OpenAI's transcription models with word-level timestamps.

## Overview

The Audio Transcription plugin automatically processes uploaded audio files and generates accurate transcriptions. It features:

- Automatic language detection
- Word-level timestamps
- Multiple transcription models (gpt-4o-mini-transcribe, whisper-1)
- Background processing via Celery

## Dependencies

- `upload` - Provides audio files to transcribe

## API Endpoints

### `GET /api/v1/plugins/audio_transcription/transcriptions`

List all transcriptions for the current user.

**Authentication:** Required (JWT token)

**Query Parameters:**
- `limit` (optional, default: 50) - Number of results
- `offset` (optional, default: 0) - Pagination offset

**Response (200):**
```json
{
  "items": [
    {
      "id": "uuid",
      "document_id": "uuid",
      "text": "Transcribed text...",
      "language": "en",
      "duration_seconds": 125.5,
      "word_count": 250,
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 10
}
```

### `GET /api/v1/plugins/audio_transcription/transcriptions/{id}`

Get a specific transcription with full details.

**Response (200):**
```json
{
  "id": "uuid",
  "document_id": "uuid",
  "text": "Full transcribed text...",
  "language": "en",
  "duration_seconds": 125.5,
  "segments": [
    {
      "id": 0,
      "start": 0.0,
      "end": 2.5,
      "text": "Hello world"
    }
  ],
  "words": [
    {"word": "Hello", "start": 0.0, "end": 0.5},
    {"word": "world", "start": 0.5, "end": 1.0}
  ],
  "created_at": "2024-01-15T10:30:00Z"
}
```

### `POST /api/v1/plugins/audio_transcription/transcriptions/{document_id}/retry`

Retry a failed transcription.

**Response (202):**
```json
{
  "status": "queued",
  "job_id": "uuid"
}
```

## Document Types

| Type | Display Name | MIME Types |
|------|--------------|------------|
| `transcription` | Transcription | application/json |

## Events

### Events Emitted

| Event | Trigger | Payload |
|-------|---------|---------|
| `job.started` | Transcription begins | `{job_id, plugin_name, document_id}` |
| `job.progress` | Progress update | `{job_id, progress, progress_message}` |
| `job.completed` | Transcription done | `{job_id, document_id, transcription_id}` |
| `job.failed` | Transcription failed | `{job_id, error_message}` |

### Events Handled

| Event | Action |
|-------|--------|
| `document.created` | Queue transcription if document type is "audio" |

## Configuration

```env
# Required
OPENAI_API_KEY=sk-your-openai-api-key

# Optional (configured in plugin settings)
# Default language (empty = auto-detect)
# Model: gpt-4o-mini-transcribe, gpt-4o-transcribe, whisper-1
```

## Plugin Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `default_language` | string | "" | Language code (e.g., "en", "pl"). Empty for auto-detect |
| `model` | string | "gpt-4o-mini-transcribe" | OpenAI model to use |

## Database Models

```
Table: transcriptions
├── id (UUID, PK)
├── document_id (FK -> documents)
├── text (TEXT) - Full transcription text
├── language (VARCHAR) - Detected/specified language
├── duration_seconds (FLOAT)
├── model_used (VARCHAR)
├── properties (JSONB) - Additional metadata
└── created_at (TIMESTAMP)

Table: transcription_words
├── id (UUID, PK)
├── transcription_id (FK -> transcriptions)
├── word (VARCHAR)
├── start_time (FLOAT)
├── end_time (FLOAT)
└── confidence (FLOAT, nullable)
```

## Background Tasks

| Task | Queue | Description |
|------|-------|-------------|
| `audio_transcription.process` | `audio_transcription` | Transcribe audio file |

## Testing

```bash
# Run all plugin tests
make test-plugin PLUGIN=audio_transcription

# Run only unit tests
cd backend && poetry run pytest plugins/audio_transcription/tests/test_unit.py

# Run only e2e tests (requires OpenAI API key)
cd backend && poetry run pytest plugins/audio_transcription/tests/test_e2e.py -v
```

## Workflow

1. User uploads audio file via Upload plugin
2. Upload plugin emits `document.created` event
3. Audio Transcription plugin receives event
4. Plugin checks if document type is "audio"
5. If yes, queues Celery task for transcription
6. Task runs, emits progress events
7. On completion, creates Transcription document (child of audio)
8. Frontend receives real-time updates via SSE

## Usage Example

```python
# Transcription happens automatically after upload
# To manually trigger transcription:

from plugins.audio_transcription.tasks import transcribe_audio

# Queue transcription job
job = transcribe_audio.delay(document_id=str(audio_document.id))

# Check status
result = job.get(timeout=300)  # Wait up to 5 minutes
```

## Error Handling

Common errors and their causes:

| Error | Cause | Solution |
|-------|-------|----------|
| "OpenAI API key not configured" | Missing OPENAI_API_KEY | Set env variable |
| "File too large" | Audio > 25MB | Use smaller files or split |
| "Unsupported format" | Invalid audio format | Convert to mp3/wav |
| "Rate limit exceeded" | Too many API calls | Wait or reduce concurrency |

## Supported Audio Formats

- MP3 (`audio/mpeg`)
- WAV (`audio/wav`)
- OGG (`audio/ogg`)
- WebM (`audio/webm`)
- FLAC (`audio/flac`)
- M4A (`audio/m4a`, `audio/x-m4a`)

## Frontend Components

| Component | Path | Description |
|-----------|------|-------------|
| TranscriptionList | /transcriptions | List all transcriptions |
| TranscriptionView | /transcriptions/:id | View transcription with word timestamps |
| RecentTranscriptionsWidget | Dashboard | Shows recent transcriptions |

## Changelog

- `1.0.0` - Initial release with OpenAI transcription support
