# Troubleshooting Guide

Ten plik zawiera rozwiązania najczęstszych problemów w UniversalAPI.

## Quick Health Check

```bash
# Szybka diagnostyka
make dev-health

# Szczegółowy status
make status

# Sprawdź porty
make dev-ports
```

## Viewing Logs

```bash
# Smart logs (auto-detects Honcho vs Manual mode)
make logs

# Konkretne komponenty
make logs-backend
make logs-frontend
make logs-celery
make logs-infra

# Real-time backend logs
tail -f backend/logs/backend.log
```

## Common Issues

### 1. Port Already in Use

**Symptom:** `Address already in use` error

**Fix:**
```bash
# Sprawdź co używa portu
lsof -i :8000   # backend
lsof -i :5173   # frontend
lsof -i :5432   # PostgreSQL
lsof -i :6379   # Redis

# Kill process na porcie
lsof -ti:8000 | xargs kill -9

# Lub użyj cleanup
make dev-clean
```

**Ports:**
- Backend: 8000
- Frontend: 5173
- PostgreSQL (dev): 5432
- PostgreSQL (test): 5433
- Redis (dev): 6379
- Redis (test): 6380

### 2. Docker Not Running

**Symptom:** `Cannot connect to Docker daemon`

**Fix:**
```bash
# Start Docker Desktop (macOS/Windows)
open -a Docker

# Wait for startup, then:
make infra-up
```

### 3. Database Connection Failed

**Symptom:** `Connection refused` to PostgreSQL

**Fixes:**

```bash
# 1. Check if PostgreSQL is running
docker ps | grep postgres

# 2. If not running:
make infra-up

# 3. Check connection
docker exec -it universalapi-postgres psql -U universalapi

# 4. Reset database (DESTRUCTIVE)
make db-reset
```

### 4. Migrations Out of Sync

**Symptom:** `relation does not exist` or model/DB mismatch

**Fix:**
```bash
# Check pending migrations
cd backend && poetry run alembic current
cd backend && poetry run alembic heads

# Apply pending
make db-migrate

# Nuclear option (DESTRUCTIVE - loses data)
make db-reset
```

### 5. Celery Tasks Not Running

**Symptom:** Jobs stuck in "pending" status

**Fixes:**

```bash
# 1. Check Celery worker
make logs-celery

# 2. Check Redis
redis-cli -n 1 PING

# 3. List queued tasks
redis-cli -n 1 KEYS "celery*"

# 4. Restart Celery
make celery-restart

# 5. Purge stuck tasks (DESTRUCTIVE)
cd backend && poetry run celery -A app.core.queue.celery_app purge -f
```

### 6. Plugin Not Loading

**Symptom:** Plugin routes return 404

**Fixes:**

```bash
# 1. Check if plugin is enabled
grep PLUGINS_ENABLED backend/.env

# 2. Check plugin structure
ls -la backend/plugins/my_plugin/

# 3. Check for import errors
cd backend && poetry run python -c "from plugins.my_plugin import plugin"

# 4. Check startup logs
make logs-backend | grep -i plugin

# 5. Restart backend
make restart-all
```

### 7. Frontend Build Errors

**Symptom:** TypeScript or build errors

**Fixes:**

```bash
# 1. Clear node_modules
cd frontend && rm -rf node_modules && npm install

# 2. Clear Vite cache
cd frontend && rm -rf .vite

# 3. TypeScript errors
cd frontend && npm run typecheck

# 4. Lint errors
cd frontend && npm run lint
```

### 8. Auth/JWT Issues

**Symptom:** 401 Unauthorized errors

**Fixes:**

```bash
# 1. Check if admin user exists
cd backend && poetry run python -c "
from app.core.database.session import sync_engine
from sqlalchemy import text
with sync_engine.connect() as conn:
    result = conn.execute(text('SELECT email FROM users'))
    print([r[0] for r in result])
"

# 2. Create admin user
make dev-setup

# 3. Check JWT settings
grep JWT backend/.env

# 4. Clear browser localStorage (frontend)
# In browser console: localStorage.clear()
```

### 9. SSE Connection Issues

**Symptom:** Real-time updates not working

**Fixes:**

```bash
# 1. Check SSE endpoint
curl -N http://localhost:8000/api/v1/events/stream

# 2. Check Redis pub/sub
redis-cli SUBSCRIBE events

# 3. Restart backend (SSE connections are persistent)
make restart-all
```

### 10. Tests Failing

**Symptom:** Tests pass locally but fail in CI (or vice versa)

**Fixes:**

```bash
# 1. Ensure test DB is running
make test-db-up

# 2. Check for port conflicts
make dev-ports

# 3. Run with verbose output
cd backend && poetry run pytest -v -s

# 4. Run specific failing test
cd backend && poetry run pytest tests/path/to/test.py::test_name -v

# 5. Reset test database
docker compose -f docker-compose.test.yml down -v
make test-db-up
```

## Force Cleanup

Gdy wszystko inne zawodzi:

```bash
# Full cleanup
make dev-clean

# This does:
# - Kills all backend/frontend/celery processes
# - Stops all Docker containers
# - Cleans up orphaned processes

# Then restart fresh:
make start-all
```

## Debug Mode

### Backend Debug Logs

```bash
# Enable debug logging
echo "LOG_LEVEL=DEBUG" >> backend/.env
make restart-all

# View detailed logs
make logs-backend
```

### Frontend Debug

```bash
# Browser console
localStorage.debug = '*'

# Check network requests
# Open DevTools -> Network tab
```

### Celery Debug

```bash
# Run Celery in foreground with debug
cd backend && poetry run celery -A app.core.queue.celery_app worker --loglevel=DEBUG
```

## Performance Issues

### Slow API Responses

```bash
# 1. Check if N+1 queries
# Enable SQL echo
echo "SQLALCHEMY_ECHO=true" >> backend/.env

# 2. Check Redis latency
redis-cli --latency

# 3. Check PostgreSQL connections
docker exec -it universalapi-postgres psql -U universalapi -c "SELECT count(*) FROM pg_stat_activity"
```

### High Memory Usage

```bash
# Check Docker stats
docker stats

# Restart containers
make infra-restart
```

## Getting Help

1. Check logs first: `make logs`
2. Check status: `make status`
3. Try cleanup: `make dev-clean && make start-all`
4. Check GitHub issues for known problems
