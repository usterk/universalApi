# UniversalAPI Backend

Backend for UniversalAPI - a universal data processing system with plugin architecture.

## Features

- **Plugin System**: Modular architecture with autodiscovery and dependency resolution
- **Event-Driven**: Real-time processing with SSE (Server-Sent Events)
- **AI Integration**: OpenAI gpt-4o-mini-transcribe for audio transcription
- **Queue System**: Celery + Redis for background processing
- **Multi-User**: JWT authentication with role-based access control
- **API Keys**: Per-source API keys for device authentication

## Tech Stack

- FastAPI
- SQLAlchemy 2.0 (async)
- PostgreSQL with pgvector
- Celery + Redis
- OpenAI API
- Alembic migrations

## Setup

```bash
# Install dependencies
poetry install

# Run migrations
poetry run alembic upgrade head

# Start development server
poetry run uvicorn app.main:app --reload
```

## Environment Variables

Create a `.env` file:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/universalapi
DATABASE_URL_SYNC=postgresql://postgres:postgres@localhost:5432/universalapi
REDIS_URL=redis://localhost:6379/0

SECRET_KEY=your-secret-key-here
OPENAI_API_KEY=your-openai-key

STORAGE_LOCAL_PATH=./storage
```

## Architecture

See the main project documentation for architecture details.
