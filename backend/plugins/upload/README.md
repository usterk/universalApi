# Plugin: Upload

Core plugin responsible for file upload and storage management.

## Overview

The Upload plugin is the foundation of the UniversalAPI file processing system. It handles:

- File uploads via REST API
- Storage management (local filesystem or S3)
- Document record creation
- Event emission for downstream processing

This is a **base plugin** with no dependencies - other plugins depend on it.

## Dependencies

None. This is a base plugin.

## API Endpoints

### `POST /api/v1/plugins/upload/files`

Upload a new file to the system.

**Authentication:** Required (JWT token or API key)

**Request:**
```http
Content-Type: multipart/form-data

file: <binary>
```

**Response (201):**
```json
{
  "document_id": "uuid",
  "filename": "example.mp3",
  "content_type": "audio/mpeg",
  "size_bytes": 12345678,
  "document_type": "audio",
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Error Responses:**
- `401` - Unauthorized (missing or invalid token)
- `413` - File too large (max 100MB)
- `422` - Missing file

### `GET /api/v1/plugins/upload/files/{document_id}`

Get metadata for an uploaded file.

**Authentication:** Required

**Response (200):**
```json
{
  "document_id": "uuid",
  "type": "audio",
  "content_type": "audio/mpeg",
  "size_bytes": 12345678,
  "filepath": "2024/01/15/uuid.mp3",
  "checksum": "sha256-hash",
  "properties": {
    "original_filename": "recording.mp3"
  },
  "created_at": "2024-01-15T10:30:00Z"
}
```

## Document Types

Document types registered by this plugin:

| Type | Display Name | MIME Types |
|------|--------------|------------|
| `audio` | Audio File | audio/mpeg, audio/mp3, audio/wav, audio/ogg, audio/webm, audio/flac, audio/m4a |
| `video` | Video File | video/mp4, video/webm, video/ogg, video/quicktime |
| `image` | Image File | image/jpeg, image/png, image/gif, image/webp, image/svg+xml |
| `text` | Text File | text/plain, text/markdown, text/html, text/csv |
| `document` | Document | application/pdf, application/msword, docx |
| `json` | JSON Data | application/json |
| `file` | Generic File | (fallback for unknown types) |

## Events

### Events Emitted

| Event | Trigger | Payload |
|-------|---------|---------|
| `document.created` | After file upload | `{document_id, document_type, content_type, size_bytes, source_id}` |

This event triggers downstream plugins (e.g., audio_transcription) to process the file.

### Events Handled

None. This is a source plugin, not a processor.

## Configuration

```env
# Storage type: "local" or "s3"
STORAGE_TYPE=local

# Local storage path (relative to backend/)
STORAGE_LOCAL_PATH=./storage

# S3 storage (if STORAGE_TYPE=s3)
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_S3_BUCKET=your-bucket
AWS_S3_REGION=us-east-1
```

## Storage Structure

Files are stored in a date-based directory structure:

```
storage/
└── 2024/
    └── 01/
        └── 15/
            ├── uuid1.mp3
            ├── uuid2.pdf
            └── uuid3.jpg
```

## Plugin Settings

Settings that can be configured per-plugin:

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `storage_type` | string | "local" | Storage backend |
| `max_file_size_mb` | integer | 100 | Maximum file size in MB |

## Testing

```bash
# Run all upload plugin tests
make test-plugin PLUGIN=upload

# Run only unit tests
cd backend && poetry run pytest plugins/upload/tests/test_unit.py

# Run only e2e tests
cd backend && poetry run pytest plugins/upload/tests/test_e2e.py -v
```

## Usage Examples

### Upload via cURL

```bash
# With JWT token
curl -X POST http://localhost:8000/api/v1/plugins/upload/files \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/file.mp3"

# With API key (for devices/sources)
curl -X POST http://localhost:8000/api/v1/plugins/upload/files \
  -H "X-API-Key: uapi_your_api_key" \
  -F "file=@/path/to/file.mp3"
```

### Upload via Python

```python
import httpx

async with httpx.AsyncClient() as client:
    with open("file.mp3", "rb") as f:
        response = await client.post(
            "http://localhost:8000/api/v1/plugins/upload/files",
            headers={"Authorization": f"Bearer {token}"},
            files={"file": f},
        )
    document = response.json()
    print(f"Uploaded: {document['document_id']}")
```

## Security Considerations

- Files are stored with UUID-based names, not original filenames
- Original filename is stored in document properties
- Checksum (SHA-256) is calculated for integrity verification
- File size is limited to prevent DoS attacks
- Files are isolated by owner (user or source)

## Changelog

- `1.0.0` - Initial release with local storage support
