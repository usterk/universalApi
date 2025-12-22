# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

UniversalAPI is a plugin-based data processing platform built with FastAPI (backend) and React (frontend). The core architecture centers around a **plugin system** where each plugin can process documents, register new document types, add API routes, define database models, and queue background tasks.

**Key Principle:** Even core functionality (like file upload) is implemented as plugins. The application is a composition of plugins orchestrated through an event-driven architecture.

## Development Commands

### First-Time Setup
```bash
# Automated setup (RECOMMENDED) - does everything in one command
make dev-setup        # Start infrastructure + install deps + migrate + create admin user

# Or manual setup:
make infra-up         # Start Docker (PostgreSQL + Redis)
make dev-install      # Install both backend and frontend dependencies
make db-migrate       # Run database migrations

# Admin credentials (created by dev-setup):
# Email: admin@example.com
# Password: admin123
```

### Daily Development

**Primary Mode: Honcho (RECOMMENDED)**
```bash
make start-all        # Start everything in background (RECOMMENDED)
                      # - Starts all services
                      # - Shows status (what started, what didn't)
                      # - Displays log locations
                      # - Returns control to terminal
make restart-all      # Restart all services ~8s
make stop-all         # Stop everything
make status           # Show detailed status
make logs             # View logs (auto-detects mode)
```

**Quick Commands**
```bash
make dev-health       # Quick health check
make dev-ports        # Show port usage
make dev-clean        # Force cleanup (troubleshooting)
```

**Manual Mode (Advanced - Individual Component Control)**
```bash
# First start infrastructure:
make infra-up         # Start Docker (PostgreSQL + Redis)

# Then start components individually:
make backend-start    # Start backend only
make frontend-start   # Start frontend only
make celery-start     # Start Celery worker + beat

# Or restart individual components:
make backend-restart  # Restart backend only ~5s
make frontend-restart # Restart frontend only ~2s
make celery-restart   # Restart Celery only ~2s
make infra-restart    # Restart Docker only ~3s
```

**Note:** Component commands require Docker to be running separately via `make infra-up`. For normal development, use `make start-all` instead.

### Working with Migrations
```bash
# Create a new migration after changing models
make db-migrate-create NAME="description_of_change"

# Apply pending migrations
make db-migrate

# Rollback last migration
make db-migrate-rollback

# Reset database (DESTRUCTIVE - drops all data)
make db-reset
```

### Testing and Quality
```bash
# All tests
make test-all          # Run all tests (core + plugins)
make test-with-coverage # Run with HTML coverage report

# Core tests only
make test-core         # Tests in backend/tests/

# Plugin tests
make test-plugins      # All plugin tests
make test-plugin PLUGIN=upload  # Specific plugin tests
make test-e2e          # Run only e2e tests

# Test database
make test-db-up        # Start test PostgreSQL on port 5433
make test-db-stop      # Stop test database

# Linting
make lint              # Run ruff (backend) + eslint (frontend)
make format            # Format code with ruff
make typecheck         # Run type checking (mypy)
```

### Environment Status
```bash
make status           # Show detailed status (versions, services, uptime, logs)
make dev-status       # Alias for status
make dev-health       # Quick health check (fast)
```

### Troubleshooting
```bash
# View logs
make logs             # Smart logs (auto-detects Honcho vs Manual mode)
make logs-backend     # Backend logs only
make logs-frontend    # Frontend logs only
make logs-celery      # Celery logs only
make logs-infra       # Docker logs only

# Status and diagnostics
make dev-health       # Quick health check
make dev-ports        # Show which ports are in use
make status           # Detailed status

# Force cleanup
make dev-clean        # Kill all processes + stop Docker
make stop-all         # Stop all services gracefully

# Check backend is running
curl http://localhost:8000/api/v1/auth/login

# Kill process on port (if needed)
lsof -ti:8000 | xargs kill -9

# Restart after code changes
make restart-all      # Restart everything (RECOMMENDED - per CLAUDE.md)
```

## Architecture Essentials

### Plugin System

Plugins are the heart of the application. Each plugin lives in `/backend/plugins/{plugin_name}/` and inherits from `BasePlugin`.

**Plugin Discovery and Loading:**
1. On startup, `PluginLoader` scans `/backend/plugins/` directory
2. Extracts metadata from each plugin (name, version, dependencies, input/output types, priority)
3. Performs topological sort based on dependencies
4. Loads plugins in dependency order
5. Registers routes at `/api/v1/plugins/{plugin_name}/*`
6. Registers event handlers with the event bus
7. Calls `on_startup()` lifecycle hooks

**Plugin Structure:**
```
plugins/my_plugin/
├── __init__.py
├── plugin.py          # Main plugin class (inherits BasePlugin)
├── models.py          # SQLAlchemy models (optional)
├── router.py          # FastAPI routes (optional)
├── tasks.py           # Celery tasks (optional)
└── handlers.py        # Event handlers (optional)
```

**Key Plugin Concepts:**
- **Dependencies:** Plugins can depend on other plugins (e.g., `audio_transcription` depends on `upload`)
- **Priority:** Lower numbers run first (deterministic processing order)
- **Input/Output Types:** Plugins declare which document types they process and produce
- **Concurrency:** Each plugin can set `max_concurrent_jobs` for rate limiting

**Example Plugins:**
- `upload`: Base plugin for file storage (local or S3), no input types
- `audio_transcription`: Processes audio documents → creates transcription documents

### Document System

Documents are the universal data container. Everything is a document: uploaded files, transcriptions, analyses, etc.

**Document Model:**
```python
Document
├── type_id           # FK to DocumentType (dynamic, registered by plugins)
├── owner_id          # FK to User
├── source_id         # FK to Source (if uploaded from external source)
├── parent_id         # FK to Document (if generated from another document)
├── storage_plugin    # Plugin name that handles storage
├── filepath          # Relative path in storage
├── content_type      # MIME type
├── size_bytes
├── checksum          # SHA-256
└── properties        # JSONB - flexible metadata
```

**Important:** Documents form **trees** via `parent_id`. An uploaded audio file might have child documents: transcription → analysis → search index.

**Document Types:**
Dynamically registered by plugins via `get_document_types()`. Each type has:
- `name` (slug like "audio", "transcription")
- `mime_types` array
- `registered_by` (plugin name)
- Optional `metadata_schema` (JSON Schema)

### Event-Driven Processing

The EventBus coordinates plugin interactions:

1. **Document Upload** → `document.created` event emitted
2. **Event Handlers** (registered by plugins) receive the event
3. **Plugins decide** if they should process the document (based on input_types, filters, custom logic)
4. **Background Task** queued via Celery
5. **Task processes** document, creates new document, emits `job.completed`
6. **New document** triggers another `document.created` event → chain processing

**Event Types:**
- `document.created`, `document.deleted`
- `job.started`, `job.progress`, `job.completed`, `job.failed`
- `plugin.enabled`, `plugin.disabled`

**SSE (Server-Sent Events):**
- Real-time event stream at `/api/v1/events/stream`
- Frontend subscribes to see live processing updates
- Events buffered (last 1000 or 15 minutes) for reconnection

### Database Architecture

**Two-Level Migration System:**
1. **Core migrations** in `/backend/alembic/versions/` - users, documents, sources, plugins
2. **Plugin migrations** - plugins can create their own tables (e.g., `0b5913df4a79_add_audio_transcription_tables.py`)

**Session Management:**
- Async SQLAlchemy with asyncpg driver
- Dependency injection via `get_db()` → yields `AsyncSession`
- Always use `async with` or FastAPI dependency for transactions

**Important Models:**
- `User`, `Role`, `Permission` (RBAC)
- `Source` (external data sources with API keys)
- `Document`, `DocumentType`
- `PluginConfig`, `PluginFilter`, `ProcessingJob`
- Plugin-specific models (e.g., `Transcription`, `TranscriptionWord`)

### Testing Architecture

Tests follow a **plugin-centric structure** - plugin tests live close to plugin code, but all tests are runnable from one place.

**Directory Structure:**
```
backend/
├── tests/                        # Core tests
│   ├── conftest.py               # Shared fixtures (CRITICAL)
│   ├── unit/
│   │   ├── test_auth.py
│   │   └── test_documents.py
│   ├── integration/
│   │   ├── test_api_auth.py
│   │   └── test_plugin_loading.py
│   └── fixtures/
│       └── factories.py
│
└── plugins/
    ├── upload/
    │   ├── plugin.py
    │   ├── README.md             # REQUIRED: Plugin documentation
    │   └── tests/                # Plugin tests CLOSE to code
    │       ├── conftest.py       # Imports from tests.conftest
    │       ├── test_unit.py
    │       └── test_e2e.py       # REQUIRED: E2E tests
    │
    └── audio_transcription/
        ├── plugin.py
        ├── README.md
        └── tests/
            ├── conftest.py
            ├── test_unit.py
            └── test_e2e.py
```

**Key Configuration (`pyproject.toml`):**
```toml
[tool.pytest.ini_options]
testpaths = ["tests", "plugins"]  # Discovers tests in both locations
markers = [
    "e2e: end-to-end tests",
    "plugin: plugin-specific tests",
]
```

**Shared Fixtures (`tests/conftest.py`):**
- `db_session` - Async SQLAlchemy session (auto-rollback)
- `async_client` - httpx AsyncClient for API tests
- `test_user`, `test_admin` - Test user fixtures
- `auth_headers` - JWT auth headers
- `mock_event_bus` - Mocked EventBus

**Plugin conftest.py Pattern:**
```python
# plugins/my_plugin/tests/conftest.py
import pytest
from tests.conftest import *  # noqa: Import shared fixtures

@pytest.fixture
def plugin_specific_fixture():
    """Plugin-specific test fixture."""
    return ...
```

**Test Database:**
- Runs on port 5433 (not 5432) to avoid conflicts
- Started via `make test-db-up` or `docker-compose.test.yml`
- Uses tmpfs for speed (no persistent storage)

### Authentication

**Dual Authentication:**
1. **JWT tokens** (for web UI) - Bearer token in Authorization header
2. **API keys** (for external sources/devices) - X-API-Key header

**Dependency Injection:**
```python
from app.core.auth.dependencies import CurrentUser, CurrentActiveUser, CurrentSuperuser, CurrentSource

async def my_endpoint(user: CurrentUser):  # Requires valid JWT
    ...

async def upload_endpoint(source: CurrentSource):  # Requires valid API key
    ...
```

**Password Hashing:**
- Uses `bcrypt` 4.0 (NOT passlib)
- Functions: `hash_password()`, `verify_password()` in `core/auth/password.py`

### Frontend Architecture

**State Management:**
- **Zustand** for auth state (persisted to localStorage)
- **TanStack Query** for API data fetching and caching

**Routing:**
- React Router v6 with route guards:
  - `ProtectedRoute` - requires JWT token
  - `PublicRoute` - redirects authenticated users

**API Client (`core/api/client.ts`):**
- Axios with automatic token refresh on 401
- Request interceptor adds Bearer token
- Response interceptor handles token expiration

**UI Framework:**
- Radix UI (unstyled accessible components)
- Tailwind CSS for styling
- shadcn/ui component library
- Lucide React for icons

## Critical Patterns and Conventions

### Field Naming: `properties` not `metadata`

**CRITICAL:** SQLAlchemy reserves the `metadata` attribute. All flexible JSON fields are named `properties`:

```python
# Backend models
class Document(Base):
    properties: Mapped[dict] = mapped_column(JSONB, default=dict)

class Source(Base):
    properties: Mapped[dict] = mapped_column(JSONB, default=dict)

# API responses
class DocumentResponse(BaseModel):
    properties: dict

# Frontend TypeScript
interface Document {
    properties: Record<string, unknown>
}
```

When storing file metadata:
```python
document = Document(
    properties={
        "original_filename": file.filename,
        "mime_type": file.content_type,
        # ... other metadata
    }
)
```

### Async/Await Throughout

**Backend:**
- All database operations are async
- All I/O operations are async
- Event handlers can be async or sync
- Celery tasks wrap async code with `asyncio.run()`

```python
# Correct
async def get_document(db: AsyncSessionDep, doc_id: UUID):
    result = await db.execute(select(Document).where(Document.id == doc_id))
    return result.scalar_one_or_none()

# Incorrect - will fail
def get_document(db: AsyncSessionDep, doc_id: UUID):
    result = db.execute(...)  # Missing await
```

### Plugin Registration

When creating a new plugin:

1. Create directory in `/backend/plugins/{plugin_name}/`
2. Implement `plugin.py` with class inheriting from `BasePlugin`
3. Define `metadata` property with all required fields
4. Implement optional methods: `get_router()`, `get_models()`, `get_tasks()`, `get_document_types()`
5. Add plugin name to `PLUGINS_ENABLED` in `.env` or config
6. If plugin has models, create migration: `make migrate-create NAME="add_{plugin_name}_tables"`
7. Restart backend for plugin to be discovered

**Plugin Priority Guidelines:**
- `10-19`: Storage/upload plugins
- `20-39`: Primary processing (transcription, OCR)
- `40-69`: Secondary processing (analysis, enrichment)
- `70-99`: Indexing and search
- `100+`: Automation and notifications

### Database Transactions

**Pattern 1: Using FastAPI dependency (recommended):**
```python
async def create_document(
    data: DocumentCreate,
    db: AsyncSessionDep,  # Auto-commits on success, rollbacks on exception
):
    doc = Document(**data.model_dump())
    db.add(doc)
    # Commit happens automatically when function returns
    return doc
```

**Pattern 2: Manual transaction:**
```python
async with async_session_factory() as session:
    try:
        doc = Document(...)
        session.add(doc)
        await session.commit()
        await session.refresh(doc)
        return doc
    except Exception:
        await session.rollback()
        raise
```

### Celery Task Pattern

```python
from app.core.queue.celery_app import celery_app
from celery import shared_task

@shared_task(
    bind=True,
    name="my_plugin.process",  # Format: {plugin_name}.{task_name}
    queue="my_plugin",          # Route to dedicated queue
)
def process_document(self, document_id: str):
    # Tasks run in separate process, need to:
    # 1. Import inside task function (avoid circular imports)
    # 2. Wrap async code with asyncio.run()
    # 3. Emit events for progress tracking

    from app.core.events.bus import get_event_bus
    import asyncio

    async def _process():
        # Async logic here
        event_bus = get_event_bus()
        await event_bus.emit_sync("job.progress", ...)  # Uses Redis pub/sub

    asyncio.run(_process())
```

### Frontend Safe Property Access

Always use optional chaining for API data:

```typescript
// Correct - safe even when data is undefined
{!data?.items?.length ? (
  <EmptyState />
) : (
  <ItemList items={data.items} />
)}

// Incorrect - will throw error if data is undefined
{data.items.length === 0 ? <EmptyState /> : <ItemList />}
```

## Common Development Tasks

### Adding a New API Endpoint

1. Add route to appropriate router in `/backend/app/api/v1/` or plugin's `router.py`
2. Use dependency injection for auth and database session
3. Define Pydantic models for request/response
4. Add corresponding function to `/frontend/src/core/api/client.ts`
5. Use in React component via TanStack Query

### Creating a New Plugin

**REQUIRED for every plugin:**
1. `plugin.py` - Main plugin class inheriting from `BasePlugin`
2. `README.md` - Documentation (API endpoints, events, configuration)
3. `tests/` directory with:
   - `conftest.py` - imports shared fixtures
   - `test_unit.py` - unit tests
   - `test_e2e.py` - end-to-end tests (REQUIRED)

**Plugin Creation Checklist:**
1. Create directory: `/backend/plugins/{plugin_name}/`
2. Implement `plugin.py` with class inheriting from `BasePlugin`
3. Create `README.md` using template from `plugins/PLUGIN_TEMPLATE.md`
4. Create `tests/` directory with conftest.py, test_unit.py, test_e2e.py
5. Add plugin name to `PLUGINS_ENABLED` in `.env`
6. If plugin has models, create migration
7. Run `make test-plugin PLUGIN={plugin_name}` to verify tests pass
8. Restart backend

**Reference Files:**
- `backend/app/core/plugins/base.py` - BasePlugin interface
- `backend/plugins/upload/` - Example base plugin
- `backend/plugins/audio_transcription/` - Example with dependencies
- `backend/plugins/PLUGIN_TEMPLATE.md` - README template

### Adding Database Models

**For Core Models:**
1. Add model to appropriate file in `/backend/app/core/{module}/models.py`
2. Import in `/backend/app/core/database/base.py` if needed
3. Create migration: `make migrate-create NAME="add_my_table"`
4. Review and edit migration in `/backend/alembic/versions/`
5. Apply: `make migrate`

**For Plugin Models:**
1. Add model to `/backend/plugins/{plugin_name}/models.py`
2. Return from plugin's `get_models()` method
3. Create plugin migration in `/backend/alembic/versions/`
4. Name convention: `{hash}_add_{plugin_name}_tables.py`

### Modifying Existing Models

**IMPORTANT:** SQLAlchemy reserves certain attribute names:
- `metadata` (use `properties` instead)
- `__mapper__`, `__table__`, etc.

**After changing models:**
1. Create migration: `make migrate-create NAME="update_table_description"`
2. Review autogenerated migration
3. Test migration on development DB
4. Restart backend (model changes don't hot-reload)

### Working with Events

**Emitting Events:**
```python
from app.core.events.bus import get_event_bus

event_bus = get_event_bus()
await event_bus.emit(
    event_type="document.created",
    source="upload_plugin",
    payload={"document_id": str(doc.id)},
    severity="info",
    persist=True,  # Save to database
)
```

**Subscribing to Events:**
```python
# In plugin.py
async def on_startup(self):
    event_bus = get_event_bus()
    event_bus.subscribe("document.created", self._handle_document_created)

async def _handle_document_created(self, event):
    # Handle event
    document_id = event.payload["document_id"]
    # Queue background task
    from plugins.my_plugin.tasks import process_document
    process_document.delay(document_id)
```

### Debugging Background Tasks

1. Check Celery worker logs (terminal where `make celery` runs)
2. Query `processing_jobs` table for task status
3. Use Celery Flower for monitoring (not yet configured)
4. Check Redis for queued tasks: `redis-cli -n 1 KEYS celery-task-meta-*`

### Restarting After Changes

**Must restart backend when:**
- Adding/modifying plugins
- Changing database models
- Changing event handlers
- Modifying application config

**Hot-reload works for:**
- Route handlers (FastAPI endpoints)
- Business logic inside route handlers
- Pydantic models

**Frontend:**
- Vite hot-reloads automatically
- Refresh browser if state gets corrupted

## Configuration

**Environment Variables:**
Create `.env` file in `/backend/`:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://universalapi:universalapi@localhost:5432/universalapi
DATABASE_URL_SYNC=postgresql://universalapi:universalapi@localhost:5432/universalapi

# Redis & Celery
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# Auth
SECRET_KEY=your-secret-key-change-in-production
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI Services
OPENAI_API_KEY=sk-...

# Storage
STORAGE_TYPE=local  # or "s3"
STORAGE_LOCAL_PATH=./storage

# Plugins
PLUGINS_ENABLED=["upload", "audio_transcription"]

# CORS
CORS_ORIGINS=["http://localhost:5173", "http://localhost:3000"]

# Logging (optional)
LOG_LEVEL=INFO           # DEBUG, INFO, WARNING, ERROR
LOG_FORMAT=auto          # auto, console, json
LOGS_DIR=./logs          # Directory for log files
LOG_TO_FILE=false        # Enable file logging
```

**Logging:**
- Development: Human-readable colored console output
- Production: JSON format for log aggregation
- File logging with rotation (10MB, 5 backups) when `LOG_TO_FILE=true`
- Logs directory is already in `.gitignore`

## Important Notes

- **Poetry Environment:** Poetry creates virtualenvs in cache directory (`~/Library/Caches/pypoetry/virtualenvs/` on macOS), not in project directory
- **Port Conflicts:** Backend runs on 8000, frontend on 5173. Use `lsof -ti:PORT | xargs kill -9` to kill processes
- **Database Naming:** Database and user both named `universalapi` (see docker-compose.yml)
- **Admin Credentials:** Default admin user is `admin@example.com` / `admin123`
- **API Documentation:** FastAPI auto-generates docs at `/api/docs` (Swagger UI)
- **SSE Connections:** Frontend maintains persistent SSE connection for real-time updates
- **Transaction Safety:** FastAPI dependency injection handles commits/rollbacks automatically
- **bcrypt Version:** Must use bcrypt 4.0+ (not passlib)

## Project-Specific Instructions

**na koniec jak zapowiadasz ze skonczyles, a zmieniales kod to zrob koniecznie restart aplikacji.**

When you finish work and have made code changes, always restart the application. This ensures all changes (especially plugin registration, model changes, and event handlers) are properly loaded.
