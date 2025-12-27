# Commands Reference

Pełna lista komend `make` dla UniversalAPI.

## Quick Reference

| Potrzebujesz | Komenda |
|--------------|---------|
| Start wszystkiego | `make start-all` |
| Stop wszystkiego | `make stop-all` |
| Restart po zmianach | `make restart-all` |
| Sprawdź status | `make status` |
| Szybka diagnostyka | `make dev-health` |
| Zobacz logi | `make logs` |
| Uruchom testy | `make test-all` |

## Setup & Installation

### First-Time Setup

```bash
make dev-setup     # RECOMMENDED - does everything
                   # - Starts Docker (PostgreSQL + Redis)
                   # - Installs backend dependencies (Poetry)
                   # - Installs frontend dependencies (npm)
                   # - Runs database migrations
                   # - Creates admin user (admin@example.com / admin123)
```

### Manual Setup

```bash
make infra-up       # Start Docker infrastructure only
make dev-install    # Install all dependencies
make db-migrate     # Run database migrations
```

## Development Workflow

### Start/Stop (Honcho Mode - RECOMMENDED)

| Command | Description | Time |
|---------|-------------|------|
| `make start-all` | Start everything in background | ~10s |
| `make stop-all` | Stop everything gracefully | ~3s |
| `make restart-all` | Restart all services | ~8s |
| `make status` | Detailed status report | - |
| `make logs` | View logs (auto-detects mode) | - |

### Component Control (Manual Mode)

Wymaga najpierw `make infra-up`.

| Command | Description | Time |
|---------|-------------|------|
| `make infra-up` | Start Docker only | ~5s |
| `make infra-stop` | Stop Docker | ~3s |
| `make infra-restart` | Restart Docker | ~3s |
| `make backend-start` | Start backend | ~3s |
| `make backend-stop` | Stop backend | ~1s |
| `make backend-restart` | Restart backend | ~5s |
| `make frontend-start` | Start frontend | ~2s |
| `make frontend-stop` | Stop frontend | ~1s |
| `make frontend-restart` | Restart frontend | ~2s |
| `make celery-start` | Start Celery worker + beat | ~3s |
| `make celery-stop` | Stop Celery | ~1s |
| `make celery-restart` | Restart Celery | ~2s |

## Database

### Migrations

| Command | Description |
|---------|-------------|
| `make db-migrate` | Apply pending migrations |
| `make db-migrate-create NAME="desc"` | Create new migration |
| `make db-migrate-rollback` | Rollback last migration |
| `make db-reset` | **DESTRUCTIVE** - Reset database |

### Examples

```bash
# After changing a model
make db-migrate-create NAME="add_status_to_documents"
make db-migrate
make restart-all
```

## Testing

### All Tests

| Command | Description |
|---------|-------------|
| `make test-all` | Run all tests (core + plugins) |
| `make test-with-coverage` | Run with HTML coverage report |

### Targeted Tests

| Command | Description |
|---------|-------------|
| `make test-core` | Core tests only (backend/tests/) |
| `make test-plugins` | All plugin tests |
| `make test-plugin PLUGIN=upload` | Specific plugin tests |
| `make test-e2e` | End-to-end tests only |

### Test Database

| Command | Description |
|---------|-------------|
| `make test-db-up` | Start test PostgreSQL (port 5433) |
| `make test-db-stop` | Stop test database |

## Code Quality

| Command | Description |
|---------|-------------|
| `make lint` | Run ruff (backend) + eslint (frontend) |
| `make format` | Format code with ruff |
| `make typecheck` | Run mypy type checking |

## Diagnostics

| Command | Description |
|---------|-------------|
| `make status` | Detailed status (versions, services, uptime) |
| `make dev-status` | Alias for status |
| `make dev-health` | Quick health check (fast) |
| `make dev-ports` | Show which ports are in use |

## Logs

| Command | Description |
|---------|-------------|
| `make logs` | Smart logs (auto-detects Honcho vs Manual) |
| `make logs-backend` | Backend logs only |
| `make logs-frontend` | Frontend logs only |
| `make logs-celery` | Celery logs only |
| `make logs-infra` | Docker logs only |

## Cleanup

| Command | Description |
|---------|-------------|
| `make dev-clean` | Force kill all processes + stop Docker |
| `make stop-all` | Graceful stop (preferred) |

## Advanced

### Direct Poetry/npm Commands

```bash
# Backend shell
cd backend && poetry shell

# Run specific Python command
cd backend && poetry run python -c "print('hello')"

# Frontend dev server (already in start-all)
cd frontend && npm run dev

# Frontend build
cd frontend && npm run build
```

### Docker Commands

```bash
# View running containers
docker ps

# Enter PostgreSQL
docker exec -it universalapi-postgres psql -U universalapi

# Enter Redis
docker exec -it universalapi-redis redis-cli

# View Docker logs
docker compose logs -f
```

### Celery Commands

```bash
# Run worker manually (foreground)
cd backend && poetry run celery -A app.core.queue.celery_app worker -l INFO

# Run beat manually (scheduler)
cd backend && poetry run celery -A app.core.queue.celery_app beat -l INFO

# Purge all tasks
cd backend && poetry run celery -A app.core.queue.celery_app purge -f
```

## Typical Workflows

### Starting Development

```bash
# First day
make dev-setup
make start-all

# Every day after
make start-all
```

### After Code Changes

```bash
# After changing routes/business logic
# (hot-reload should work, but if not:)
make backend-restart

# After changing plugins/models/events
make restart-all

# After changing frontend
# (Vite hot-reloads automatically)
```

### After Database Model Changes

```bash
make db-migrate-create NAME="description"
# Review migration in alembic/versions/
make db-migrate
make restart-all
```

### Creating New Plugin

```bash
# 1. Create plugin files
# 2. If has models:
make db-migrate-create NAME="add_myplugin_tables"
make db-migrate

# 3. Add to .env PLUGINS_ENABLED

# 4. Test
make test-plugin PLUGIN=myplugin

# 5. Restart
make restart-all
```

### Before Committing

```bash
make lint
make typecheck
make test-all
```
