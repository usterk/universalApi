# Plugin: [Plugin Name]

> Template for plugin documentation. Copy this file and fill in the sections.

## Overview

Brief description of what this plugin does.

## Dependencies

List of plugins this plugin depends on:

- `dependency_plugin` - Why it's needed

## API Endpoints

### `POST /api/v1/plugins/[plugin_name]/endpoint`

Description of what this endpoint does.

**Authentication:** Required (JWT token)

**Request:**
```http
Content-Type: application/json

{
  "field": "value"
}
```

**Response:**
```json
{
  "id": "uuid",
  "status": "success"
}
```

**Error Responses:**
- `400` - Bad request (invalid input)
- `401` - Unauthorized
- `404` - Resource not found

### `GET /api/v1/plugins/[plugin_name]/resource/{id}`

Description of the endpoint.

**Query Parameters:**
- `param` (optional) - Description

## Document Types

Document types registered by this plugin:

| Type | MIME Types | Description |
|------|------------|-------------|
| `type_name` | `mime/type` | Description |

## Events

### Events Emitted

| Event | Trigger | Payload |
|-------|---------|---------|
| `plugin.event_name` | When X happens | `{field: value}` |

### Events Handled

| Event | Action |
|-------|--------|
| `document.created` | Process if matching type |

## Configuration

Environment variables used by this plugin:

```env
# Required
PLUGIN_API_KEY=your-api-key

# Optional
PLUGIN_SETTING=default_value
```

## Database Models

If the plugin adds database models:

```
Table: plugin_table
├── id (UUID, PK)
├── document_id (FK -> documents)
├── created_at (timestamp)
└── data (JSONB)
```

## Background Tasks

Celery tasks registered by this plugin:

| Task | Queue | Description |
|------|-------|-------------|
| `plugin.process` | `plugin_queue` | Process document |

## Testing

```bash
# Run all plugin tests
make test-plugin PLUGIN=[plugin_name]

# Run only unit tests
cd backend && poetry run pytest plugins/[plugin_name]/tests/test_unit.py

# Run only e2e tests
cd backend && poetry run pytest plugins/[plugin_name]/tests/test_e2e.py
```

## Usage Example

```python
# Example of using this plugin programmatically
from plugins.[plugin_name].service import process_document

result = await process_document(document_id)
```

## Changelog

- `1.0.0` - Initial release
