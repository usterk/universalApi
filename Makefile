# =============================================================================
# Claude Code Quick Reference
# =============================================================================
# Common scenarios and commands:
#
# ✅ Starting the app:
#    - First time:         make dev-setup && make start-all
#    - Daily development:  make start-all
#    - After code change:  make restart-all (or wait for hot-reload)
#
# ✅ Checking status:
#    - Quick check:        make dev-health
#    - Detailed status:    make status
#    - View logs:          make logs
#
# ✅ Database changes:
#    - After model change: make db-migrate-create NAME='description' && make db-migrate
#    - Reset database:     make db-reset
#
# ✅ Testing:
#    - Run all tests:      make test-all
#    - Test one plugin:    make test-plugin PLUGIN=upload
#
# ✅ Troubleshooting:
#    - Services not starting: make dev-clean && make start-all
#    - Port conflicts:        make dev-ports
#    - Check what's running:  make dev-health
#
# 🚨 AFTER CODE CHANGES: Always run 'make restart-all' (per CLAUDE.md)
# =============================================================================

# Configuration
LOGS_DIR ?= backend/logs
SHELL := /bin/bash

# Default target
.DEFAULT_GOAL := help

# =============================================================================
# .PHONY declarations
# =============================================================================
.PHONY: help help-full \
	start-all stop-all restart-all status logs \
	app-start app-restart app-stop app-logs \
	backend-start backend-restart backend-stop \
	frontend-start frontend-restart frontend-stop \
	celery-start celery-restart celery-stop \
	infra-up infra-up-tools infra-stop infra-restart infra-logs infra-health \
	dev-install dev-setup backend-install frontend-install \
	db-migrate db-migrate-create db-migrate-rollback db-reset \
	test-all test-with-coverage test-core test-plugins test-plugin test-e2e \
	test-db-up test-db-stop \
	lint format typecheck \
	logs-backend logs-frontend logs-celery logs-infra dev-status \
	dev-clean dev-health dev-ports \
	start-local restart-local stop-local local-status logs-local logs-all \
	dev stop backend-run frontend-run celery celery-beat \
	migrate migrate-create migrate-downgrade test test-cov test-db-down install \
	stop-app stop-backend stop-frontend stop-celery \
	restart-app restart-backend restart-frontend restart-celery restart-docker

# =============================================================================
# 1. Help
# =============================================================================

help:
	@echo "UniversalAPI - Development Commands"
	@echo ""
	@echo "🚀 QUICK START (Most Common):"
	@echo "  make start-all        Start everything in background (RECOMMENDED)"
	@echo "  make stop-all         Stop everything"
	@echo "  make restart-all      Restart everything"
	@echo "  make status           Show service status"
	@echo "  make logs             View logs (smart mode detection)"
	@echo ""
	@echo "📦 SETUP (First Time):"
	@echo "  make dev-setup        Complete first-time setup"
	@echo "  make dev-install      Install dependencies"
	@echo ""
	@echo "💻 DEVELOPMENT:"
	@echo "  make app-start        Start all services (Honcho)"
	@echo "  make app-restart      Restart all services"
	@echo "  make app-stop         Stop all services"
	@echo ""
	@echo "🔧 INFRASTRUCTURE:"
	@echo "  make infra-up         Start Docker (PostgreSQL + Redis)"
	@echo "  make infra-stop       Stop Docker"
	@echo "  make infra-restart    Restart Docker containers"
	@echo ""
	@echo "🗄️  DATABASE:"
	@echo "  make db-migrate                      Run migrations"
	@echo "  make db-migrate-create NAME='desc'   Create migration"
	@echo "  make db-reset                        Reset database (DESTRUCTIVE)"
	@echo ""
	@echo "🧪 TESTING:"
	@echo "  make test-all         Run all tests"
	@echo "  make test-core        Core tests only"
	@echo "  make test-plugin PLUGIN=name  Test specific plugin"
	@echo ""
	@echo "🔍 MONITORING:"
	@echo "  make status           Detailed status"
	@echo "  make dev-health       Quick health check"
	@echo "  make logs             View logs"
	@echo "  make dev-ports        Show port usage"
	@echo ""
	@echo "🛠️  TROUBLESHOOTING:"
	@echo "  make dev-clean        Force cleanup everything"
	@echo ""
	@echo "For detailed help: make help-full"

help-full:
	@echo "UniversalAPI - Complete Command Reference"
	@echo ""
	@echo "=========================================="
	@echo "QUICK START"
	@echo "=========================================="
	@echo "  start-all             Start everything (Honcho mode - RECOMMENDED)"
	@echo "  stop-all              Stop everything (app + Docker)"
	@echo "  restart-all           Restart everything"
	@echo "  status                Comprehensive status"
	@echo "  logs                  Smart logs (auto-detects mode)"
	@echo ""
	@echo "=========================================="
	@echo "DEVELOPMENT WORKFLOW (Honcho Mode)"
	@echo "=========================================="
	@echo "  app-start             Start all services with Honcho"
	@echo "  app-restart           Restart all services"
	@echo "  app-stop              Stop all services (keeps Docker)"
	@echo "  app-logs              View Honcho logs"
	@echo ""
	@echo "=========================================="
	@echo "MANUAL MODE (Advanced)"
	@echo "=========================================="
	@echo "  backend-start         Start backend only"
	@echo "  backend-restart       Restart backend only"
	@echo "  backend-stop          Stop backend only"
	@echo "  frontend-start        Start frontend only"
	@echo "  frontend-restart      Restart frontend only"
	@echo "  frontend-stop         Stop frontend only"
	@echo "  celery-start          Start Celery worker + beat"
	@echo "  celery-restart        Restart Celery"
	@echo "  celery-stop           Stop Celery"
	@echo ""
	@echo "=========================================="
	@echo "INFRASTRUCTURE (Docker)"
	@echo "=========================================="
	@echo "  infra-up              Start Docker (PostgreSQL + Redis)"
	@echo "  infra-up-tools        Start with pgAdmin + Redis Commander"
	@echo "  infra-stop            Stop Docker containers"
	@echo "  infra-restart         Restart Docker (fast, no down/up)"
	@echo "  infra-logs            View Docker logs"
	@echo "  infra-health          Check infrastructure health"
	@echo ""
	@echo "=========================================="
	@echo "INSTALLATION & SETUP"
	@echo "=========================================="
	@echo "  dev-install           Install all dependencies"
	@echo "  dev-setup             First-time setup (infra + deps + migrate + admin)"
	@echo "  backend-install       Install backend dependencies"
	@echo "  frontend-install      Install frontend dependencies"
	@echo ""
	@echo "=========================================="
	@echo "DATABASE"
	@echo "=========================================="
	@echo "  db-migrate            Run database migrations"
	@echo "  db-migrate-create     Create new migration (NAME=description)"
	@echo "  db-migrate-rollback   Rollback last migration"
	@echo "  db-reset              Reset database (DESTRUCTIVE)"
	@echo ""
	@echo "=========================================="
	@echo "TESTING"
	@echo "=========================================="
	@echo "  test-all              Run all tests (core + plugins)"
	@echo "  test-with-coverage    Run tests with coverage report"
	@echo "  test-core             Run only core tests"
	@echo "  test-plugins          Run all plugin tests"
	@echo "  test-plugin           Run specific plugin (PLUGIN=upload)"
	@echo "  test-e2e              Run only e2e tests"
	@echo "  test-db-up            Start test database"
	@echo "  test-db-stop          Stop test database"
	@echo ""
	@echo "=========================================="
	@echo "CODE QUALITY"
	@echo "=========================================="
	@echo "  lint                  Run linters (ruff + eslint)"
	@echo "  format                Format code with ruff"
	@echo "  typecheck             Run type checking (mypy)"
	@echo ""
	@echo "=========================================="
	@echo "LOGS & MONITORING"
	@echo "=========================================="
	@echo "  logs                  Smart logs (auto-detects mode)"
	@echo "  logs-backend          Tail backend logs"
	@echo "  logs-frontend         Tail frontend logs"
	@echo "  logs-celery           Tail Celery logs"
	@echo "  logs-infra            Tail Docker logs"
	@echo "  status                Detailed status"
	@echo "  dev-status            Alias for status"
	@echo ""
	@echo "=========================================="
	@echo "TROUBLESHOOTING"
	@echo "=========================================="
	@echo "  dev-clean             Force cleanup (kill all + stop Docker)"
	@echo "  dev-health            Quick health check"
	@echo "  dev-ports             Show port usage"
	@echo ""

# =============================================================================
# 2. Quick Start (Most Common Commands)
# =============================================================================

# Start everything (RECOMMENDED)
start-all: app-start

# Stop everything (including test databases)
stop-all: app-stop infra-stop test-db-stop
	@echo "✓ All services stopped (including test databases)."

# Restart everything (with auto log cleanup)
restart-all: stop-all logs-clean
	@sleep 2
	@$(MAKE) start-all

# Show status of all services
status:
	@$(MAKE) dev-status

# View logs (smart: auto-detects Honcho vs Manual mode)
logs:
	@if pgrep -f "honcho" >/dev/null 2>&1; then \
		echo "📋 Honcho mode detected. Showing honcho.log..."; \
		echo ""; \
		cat $(LOGS_DIR)/honcho.log 2>/dev/null || echo "No honcho logs found"; \
	elif [ -f "$(LOGS_DIR)/backend.log" ]; then \
		echo "📋 Manual mode detected. Showing all component logs..."; \
		echo ""; \
		cat $(LOGS_DIR)/*.log 2>/dev/null; \
	else \
		echo "⚠️  No services running."; \
		echo "    Run 'make start-all' first."; \
	fi

# =============================================================================
# 3. Development Workflow (Honcho Mode - RECOMMENDED)
# =============================================================================
# Honcho mode starts ALL services in ONE terminal:
# - Docker (PostgreSQL + Redis)
# - FastAPI backend
# - Vite frontend
# - Celery worker + beat
#
# This is the PRIMARY way to run the application.
# For individual component control, see "Manual Mode" section below.
# =============================================================================

# Start all services with Honcho (one terminal)
app-start:
	@echo "🚀 Starting UniversalAPI in background..."
	@echo ""

	@# 1. Force cleanup ports FIRST (critical fix)
	@echo "🧹 Cleaning up ports and processes..."
	@-lsof -ti:8000 2>/dev/null | xargs kill -9 2>/dev/null || true
	@-lsof -ti:5173 2>/dev/null | xargs kill -9 2>/dev/null || true
	@sleep 1

	@# 2. Stop any existing services (idempotent)
	@-pkill -9 -f "uvicorn app.main:app" 2>/dev/null || true
	@-pkill -9 -f "celery -A app.core.queue" 2>/dev/null || true
	@-pkill -9 -f "npm run dev" 2>/dev/null || true
	@-pkill -9 -f "vite" 2>/dev/null || true
	@-pkill -9 -f "honcho" 2>/dev/null || true
	@sleep 2

	@# 3. Ensure logs directory AND files exist (prevents tee race condition)
	@mkdir -p $(LOGS_DIR)
	@touch $(LOGS_DIR)/backend.log
	@touch $(LOGS_DIR)/frontend.log
	@touch $(LOGS_DIR)/celery_worker.log
	@touch $(LOGS_DIR)/celery_beat.log
	@touch $(LOGS_DIR)/honcho.log

	@# 4. Start Honcho (which will start Docker containers)
	@nohup sh -c 'cd backend && poetry run honcho start -f ../Procfile.local' > $(LOGS_DIR)/honcho.log 2>&1 &
	@echo ""
	@echo "⏳ Waiting for services to start..."

	@# 5. Wait for Docker health (Docker is started by Honcho)
	@./scripts/wait-for-services.sh || (echo "❌ Docker services failed to become healthy" && exit 1)

	@# 6. Smart wait for backend health (up to 20 seconds)
	@bash -c 'for i in {1..20}; do \
		if curl -s http://localhost:8000/health > /dev/null 2>&1; then \
			echo "✓ Backend is ready"; \
			break; \
		fi; \
		sleep 1; \
	done'

	@# 7. Display status
	@echo ""
	@echo "=========================================="
	@echo "SERVICE STATUS:"
	@echo "=========================================="
	@$(MAKE) dev-health
	@echo ""
	@echo "=========================================="
	@echo "LOGS:"
	@echo "=========================================="
	@echo "  📁 Location: $(CURDIR)/$(LOGS_DIR)/"
	@echo "  📋 Main log: $(LOGS_DIR)/honcho.log"
	@echo ""
	@echo "  View logs:"
	@echo "    make logs           # All logs (smart)"
	@echo "    make logs-backend   # Backend only"
	@echo "    make logs-frontend  # Frontend only"
	@echo "    make logs-celery    # Celery only"
	@echo ""
	@echo "=========================================="
	@echo "CONTROLS:"
	@echo "=========================================="
	@echo "  Stop all:     make stop-all"
	@echo "  Restart all:  make restart-all"
	@echo "  Check status: make dev-health"
	@echo ""

	@# 8. Verify critical services are running (improved check)
	@if pgrep -f "honcho" >/dev/null 2>&1 && pgrep -f "uvicorn app.main" >/dev/null 2>&1; then \
		echo "✅ All services started successfully!"; \
	else \
		echo "❌ ERROR: Services failed to start properly!"; \
		echo ""; \
		echo "Honcho process: $$(pgrep -f 'honcho' >/dev/null 2>&1 && echo '✓ Running' || echo '✗ Not found')"; \
		echo "Backend process: $$(pgrep -f 'uvicorn app.main' >/dev/null 2>&1 && echo '✓ Running' || echo '✗ Not found')"; \
		echo ""; \
		echo "Last 20 lines of honcho.log:"; \
		tail -20 $(LOGS_DIR)/honcho.log; \
		exit 1; \
	fi
	@echo ""

# Restart all services
app-restart: app-stop
	@sleep 2
	@$(MAKE) app-start

# Stop all services (keeps Docker running)
app-stop:
	@echo "⏹️  Stopping all app components..."
	@-pkill -9 -f "uvicorn app.main:app" 2>/dev/null || true
	@-pkill -9 -f "celery -A app.core.queue" 2>/dev/null || true
	@-pkill -9 -f "npm run dev" 2>/dev/null || true
	@-pkill -9 -f "vite" 2>/dev/null || true
	@-pkill -9 -f "honcho" 2>/dev/null || true
	@-lsof -ti:8000 | xargs kill -9 2>/dev/null || true
	@sleep 0.5
	@echo "✓ All app components stopped (Docker still running)."

# View Honcho logs
app-logs:
	@cat $(LOGS_DIR)/honcho.log 2>/dev/null || echo "No honcho logs found. Is app running?"

# =============================================================================
# 4. Manual Mode (Advanced - Individual Component Control)
# =============================================================================
# Use these commands to control individual components.
# REQUIRES: Infrastructure running first (make infra-up)
#
# This mode is for advanced users who need fine-grained control.
# For normal development, use 'make start-all' instead.
# =============================================================================

# Helper function to check if infrastructure is running
define check_infra_running
	@if ! docker ps | grep -q universalapi_postgres; then \
		echo "❌ ERROR: Infrastructure not running. Run 'make infra-up' first."; \
		exit 1; \
	fi
endef

# Backend
backend-start:
	@echo "⚙️  Starting backend..."
	$(call check_infra_running)
	@# Stop existing backend first (idempotent)
	@-pkill -f "uvicorn app.main:app" 2>/dev/null || true
	@sleep 0.5
	@mkdir -p $(LOGS_DIR)
	@cd backend && poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 >> ../$(LOGS_DIR)/backend.log 2>&1 &
	@echo "✓ Backend started. Logs: $(LOGS_DIR)/backend.log"

backend-restart:
	@$(MAKE) backend-stop
	@sleep 1
	@$(MAKE) backend-start

backend-stop:
	@echo "⏹️  Stopping backend..."
	@-pkill -f "uvicorn app.main:app" 2>/dev/null || true
	@echo "✓ Backend stopped."

# Frontend
frontend-start:
	@echo "⚙️  Starting frontend..."
	@# Stop existing frontend first (idempotent)
	@-pkill -f "vite" 2>/dev/null || true
	@-pkill -f "npm run dev" 2>/dev/null || true
	@sleep 0.5
	@mkdir -p $(LOGS_DIR)
	@cd frontend && npm run dev >> ../$(LOGS_DIR)/frontend.log 2>&1 &
	@echo "✓ Frontend started. Logs: $(LOGS_DIR)/frontend.log"

frontend-restart:
	@$(MAKE) frontend-stop
	@sleep 1
	@$(MAKE) frontend-start

frontend-stop:
	@echo "⏹️  Stopping frontend..."
	@-pkill -f "vite" 2>/dev/null || true
	@-pkill -f "npm run dev" 2>/dev/null || true
	@echo "✓ Frontend stopped."

# Celery
celery-start:
	@echo "⚙️  Starting Celery worker and beat..."
	$(call check_infra_running)
	@# Stop existing Celery first (idempotent)
	@-pkill -f "celery -A app.core.queue" 2>/dev/null || true
	@sleep 0.5
	@mkdir -p $(LOGS_DIR)
	@cd backend && poetry run celery -A app.core.queue.celery_app worker --loglevel=info >> ../$(LOGS_DIR)/celery_worker.log 2>&1 &
	@cd backend && poetry run celery -A app.core.queue.celery_app beat --loglevel=info >> ../$(LOGS_DIR)/celery_beat.log 2>&1 &
	@echo "✓ Celery started. Logs: $(LOGS_DIR)/celery_*.log"

celery-restart:
	@$(MAKE) celery-stop
	@sleep 1
	@$(MAKE) celery-start

celery-stop:
	@echo "⏹️  Stopping Celery..."
	@-pkill -f "celery -A app.core.queue" 2>/dev/null || true
	@echo "✓ Celery stopped."

# =============================================================================
# 5. Infrastructure (Docker)
# =============================================================================

# Start Docker containers (PostgreSQL + Redis)
infra-up:
	@echo "🐳 Starting infrastructure (PostgreSQL + Redis)..."
	@docker compose up -d
	@echo "   Waiting for health checks..."
	@sleep 3
	@$(MAKE) infra-health

# Start with dev tools (pgAdmin, Redis Commander)
infra-up-tools:
	@echo "🐳 Starting infrastructure with dev tools..."
	@docker compose -f docker-compose.yml -f docker-compose.dev.yml --profile tools up -d
	@sleep 3
	@$(MAKE) infra-health

# Stop Docker containers
infra-stop:
	@echo "⏹️  Stopping infrastructure..."
	@docker compose down
	@echo "✓ Infrastructure stopped."

# Restart Docker containers (fast - no down/up)
infra-restart:
	@echo "🔄 Restarting infrastructure..."
	@docker compose restart
	@sleep 2
	@$(MAKE) infra-health

# View Docker logs
infra-logs:
	@docker compose logs

# Quick health check
infra-health:
	@echo "Infrastructure Health:"
	@docker compose ps

# =============================================================================
# 6. Installation & Setup
# =============================================================================

# Install all dependencies (backend + frontend)
dev-install: backend-install frontend-install
	@echo "✓ All dependencies installed!"

# Install backend dependencies
backend-install:
	@echo "📦 Installing backend dependencies..."
	@cd backend && poetry install
	@echo "✓ Backend dependencies installed."

# Install frontend dependencies
frontend-install:
	@echo "📦 Installing frontend dependencies..."
	@cd frontend && npm install
	@echo "✓ Frontend dependencies installed."

# First-time setup (RECOMMENDED for new developers)
dev-setup: infra-up backend-install frontend-install db-migrate
	@echo ""
	@echo "=========================================="
	@echo "Creating default admin user..."
	@echo "=========================================="
	@echo "INSERT INTO users (id, email, hashed_password, full_name, is_active, is_superuser, role_id, created_at, updated_at) VALUES (gen_random_uuid(), 'admin@example.com', '\$$2b\$$12\$$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyKuL6oG7K6i', 'Admin User', true, true, (SELECT id FROM roles WHERE name = 'admin' LIMIT 1), NOW(), NOW()) ON CONFLICT (email) DO NOTHING;" | docker exec -i $$(docker ps -q -f name=postgres) psql -U universalapi -d universalapi 2>/dev/null || echo "Admin user may already exist"
	@echo ""
	@echo "=========================================="
	@echo "✓ Setup complete!"
	@echo "=========================================="
	@echo ""
	@echo "Admin credentials:"
	@echo "  Email:    admin@example.com"
	@echo "  Password: admin123"
	@echo ""
	@echo "Next steps:"
	@echo "  1. Run: make start-all"
	@echo "  2. Visit: http://localhost:5173"
	@echo "  3. Check API docs: http://localhost:8000/api/docs"
	@echo ""

# =============================================================================
# 7. Database
# =============================================================================

# Run migrations
db-migrate:
	@echo "🗄️  Running database migrations..."
	@cd backend && poetry run alembic upgrade head
	@echo "✓ Migrations complete."

# Create new migration
db-migrate-create:
ifndef NAME
	$(error ❌ NAME is required. Usage: make db-migrate-create NAME='description')
endif
	@echo "📝 Creating migration: $(NAME)"
	@cd backend && poetry run alembic revision --autogenerate -m "$(NAME)"
	@echo "✓ Migration created."

# Rollback last migration
db-migrate-rollback:
	@echo "⏪ Rolling back last migration..."
	@cd backend && poetry run alembic downgrade -1
	@echo "✓ Migration rolled back."

# Reset database (DESTRUCTIVE - drops all data)
db-reset:
	@echo "⚠️  WARNING: This will DELETE ALL DATA in the database!"
	@echo -n "Are you sure? Type 'yes' to continue: " && read confirm && [ "$$confirm" = "yes" ]
	@echo "🗑️  Resetting database..."
	@docker exec $$(docker ps -q -f name=postgres) psql -U universalapi -d universalapi -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public; GRANT ALL ON SCHEMA public TO universalapi; GRANT ALL ON SCHEMA public TO public;"
	@$(MAKE) db-migrate
	@echo "✓ Database reset complete."

# =============================================================================
# 8. Testing
# =============================================================================

# Ensure test database is running (idempotent helper)
ensure-test-db:
	@if ! docker compose -f docker-compose.test.yml ps 2>/dev/null | grep -q "Up"; then \
		echo "📦 Test database not running, starting..."; \
		docker compose -f docker-compose.test.yml up -d; \
		sleep 2; \
		echo "✓ Test database started"; \
	fi

# Run all tests (core + plugins)
test-all: ensure-test-db
	@echo "🧪 Running all tests..."
	@cd backend && poetry run pytest

# Run tests with HTML coverage report
test-with-coverage: ensure-test-db
	@echo "🧪 Running tests with coverage..."
	@cd backend && poetry run pytest --cov=app --cov=plugins --cov-report=html --cov-report=term
	@echo "✓ Coverage report: backend/htmlcov/index.html"

# Run only core tests
test-core: ensure-test-db
	@echo "🧪 Running core tests..."
	@cd backend && poetry run pytest tests/ -v

# Run all plugin tests
test-plugins: ensure-test-db
	@echo "🧪 Running plugin tests..."
	@cd backend && poetry run pytest plugins/ -v

# Run specific plugin tests (usage: make test-plugin PLUGIN=upload)
test-plugin: ensure-test-db
ifndef PLUGIN
	$(error ❌ PLUGIN is required. Usage: make test-plugin PLUGIN=upload)
endif
	@echo "🧪 Testing plugin: $(PLUGIN)"
	@cd backend && poetry run pytest plugins/$(PLUGIN)/tests/ -v

# Run only e2e tests for all plugins
test-e2e: ensure-test-db
	@echo "🧪 Running e2e tests..."
	@cd backend && poetry run pytest plugins/ -m e2e -v

# Start test database
test-db-up:
	@echo "🐳 Starting test database..."
	@docker compose -f docker-compose.test.yml up -d
	@echo "✓ Test database running on port 5433"

# Stop test database
test-db-stop:
	@echo "⏹️  Stopping test database..."
	@docker compose -f docker-compose.test.yml down
	@echo "✓ Test database stopped."

# Frontend tests
test-frontend:
	@echo "🧪 Running frontend tests..."
	@cd frontend && npm run test:run

test-frontend-watch:
	@echo "🧪 Running frontend tests in watch mode..."
	@cd frontend && npm test

test-frontend-coverage:
	@echo "🧪 Running frontend tests with coverage..."
	@cd frontend && npm run test:coverage
	@echo "✓ Coverage report: frontend/coverage/index.html"

# Generate MSW mocks from OpenAPI
generate-mocks:
	@echo "🔄 Generating MSW handlers from OpenAPI..."
	@cd frontend && npm run generate:mocks

# Full test suite (backend + frontend)
test-full:
	@echo "🧪 Running full test suite (backend + frontend)..."
	@$(MAKE) test-all
	@$(MAKE) test-frontend
	@echo "✓ All tests complete."

# =============================================================================
# 9. Code Quality
# =============================================================================

lint:
	@echo "🔍 Running linters..."
	@cd backend && poetry run ruff check .
	@cd frontend && npm run lint
	@echo "✓ Linting complete."

format:
	@echo "✨ Formatting code..."
	@cd backend && poetry run ruff format .
	@echo "✓ Formatting complete."

typecheck:
	@echo "🔍 Running type checker..."
	@cd backend && poetry run mypy app plugins --ignore-missing-imports
	@echo "✓ Type checking complete."

# =============================================================================
# 10. Logs & Monitoring
# =============================================================================

# Component-specific logs
logs-backend:
	@cat $(LOGS_DIR)/backend.log 2>/dev/null || echo "No backend logs found"

logs-frontend:
	@cat $(LOGS_DIR)/frontend.log 2>/dev/null || echo "No frontend logs found"

logs-celery:
	@cat $(LOGS_DIR)/celery*.log 2>/dev/null || echo "No celery logs found"

logs-infra:
	@docker compose logs

logs-all:
	@echo "📋 Showing all aggregated logs (honcho.log)..."
	@cat $(LOGS_DIR)/honcho.log 2>/dev/null || echo "No honcho logs found. Start services with 'make start-all'"

# Log management commands
logs-clean:
	@echo "🗑️  Clearing all logs..."
	@for f in $(LOGS_DIR)/*.log; do \
		[ -f "$$f" ] && : > "$$f"; \
	done
	@echo "✅ Logs cleared (truncated)"

logs-rotate:
	@echo "🔄 Rotating logs..."
	@TIMESTAMP=$$(date +%Y%m%d_%H%M%S); \
	for f in $(LOGS_DIR)/*.log; do \
		[ -f "$$f" ] && [ -s "$$f" ] && \
		cp "$$f" "$$f.$$TIMESTAMP" && \
		: > "$$f"; \
	done
	@echo "✅ Logs rotated (copied and truncated)"

logs-archive:
	@echo "📦 Archiving old logs..."
	@mkdir -p $(LOGS_DIR)/archive
	@find $(LOGS_DIR) -name "*.log.*" -exec mv {} $(LOGS_DIR)/archive/ \; 2>/dev/null || true
	@echo "✅ Old logs archived to $(LOGS_DIR)/archive/"

# Comprehensive status (detailed)
dev-status:
	@echo "=========================================="
	@echo "UniversalAPI - Environment Status"
	@echo "=========================================="
	@echo ""
	@echo "📦 INSTALLED VERSIONS:"
	@echo "  Python:      $$(python3 --version 2>&1 | sed 's/Python //')"
	@echo "  Poetry:      $$(cd backend && poetry --version 2>&1 | sed 's/Poetry (version //' | sed 's/)//' || echo 'Not installed')"
	@echo "  Node:        $$(node --version 2>&1 || echo 'Not installed')"
	@echo "  npm:         $$(npm --version 2>&1 || echo 'Not installed')"
	@echo "  Docker:      $$(docker --version 2>&1 | sed 's/Docker version //' | cut -d',' -f1 || echo 'Not installed')"
	@echo "  Make:        $$(make --version 2>&1 | head -1 | sed 's/GNU Make //')"
	@echo ""
	@echo "🚀 SERVICE STATUS:"
	@if docker ps 2>/dev/null | grep -q universalapi_postgres; then \
		echo "  PostgreSQL:  ✓ Running (port 5432)"; \
		POSTGRES_UPTIME=$$(docker ps --filter "name=universalapi_postgres" --format "{{.Status}}" 2>/dev/null); \
		echo "               Uptime: $$POSTGRES_UPTIME"; \
	else \
		echo "  PostgreSQL:  ✗ Not running"; \
	fi
	@if docker ps 2>/dev/null | grep -q universalapi_redis; then \
		echo "  Redis:       ✓ Running (port 6379)"; \
		REDIS_UPTIME=$$(docker ps --filter "name=universalapi_redis" --format "{{.Status}}" 2>/dev/null); \
		echo "               Uptime: $$REDIS_UPTIME"; \
	else \
		echo "  Redis:       ✗ Not running"; \
	fi
	@if curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health --max-time 2 2>/dev/null | grep -q 200; then \
		echo "  Backend:     ✓ Running (http://localhost:8000)"; \
		BACKEND_PID=$$(pgrep -f "uvicorn.*app.main" | head -1); \
		if [ -n "$$BACKEND_PID" ]; then \
			BACKEND_UPTIME=$$(ps -o etime= -p $$BACKEND_PID 2>/dev/null | tr -d ' '); \
			echo "               PID: $$BACKEND_PID, Uptime: $$BACKEND_UPTIME"; \
		fi; \
	else \
		echo "  Backend:     ✗ Not running"; \
	fi
	@if curl -s -o /dev/null -w "%{http_code}" http://localhost:5173 --max-time 2 2>/dev/null | grep -q 200; then \
		echo "  Frontend:    ✓ Running (http://localhost:5173)"; \
		FRONTEND_PID=$$(pgrep -f "vite" | head -1); \
		if [ -n "$$FRONTEND_PID" ]; then \
			FRONTEND_UPTIME=$$(ps -o etime= -p $$FRONTEND_PID 2>/dev/null | tr -d ' '); \
			echo "               PID: $$FRONTEND_PID, Uptime: $$FRONTEND_UPTIME"; \
		fi; \
	else \
		echo "  Frontend:    ✗ Not running"; \
	fi
	@if pgrep -f "celery.*worker" >/dev/null 2>&1; then \
		echo "  Celery:      ✓ Worker running"; \
		CELERY_PID=$$(pgrep -f "celery.*worker" | head -1); \
		if [ -n "$$CELERY_PID" ]; then \
			CELERY_UPTIME=$$(ps -o etime= -p $$CELERY_PID 2>/dev/null | tr -d ' '); \
			echo "               PID: $$CELERY_PID, Uptime: $$CELERY_UPTIME"; \
		fi; \
	else \
		echo "  Celery:      ✗ Not running"; \
	fi
	@if pgrep -f "honcho" >/dev/null 2>&1; then \
		echo "  Honcho:      ✓ Running (managing all services)"; \
		HONCHO_PID=$$(pgrep -f "honcho" | head -1); \
		if [ -n "$$HONCHO_PID" ]; then \
			HONCHO_UPTIME=$$(ps -o etime= -p $$HONCHO_PID 2>/dev/null | tr -d ' '); \
			echo "               PID: $$HONCHO_PID, Uptime: $$HONCHO_UPTIME"; \
		fi; \
	fi
	@echo ""
	@echo "📝 LOGS:"
	@if [ -d "$(LOGS_DIR)" ]; then \
		echo "  Location:    $(CURDIR)/$(LOGS_DIR)/"; \
		echo "  Files:"; \
		ls $(LOGS_DIR)/*.log >/dev/null 2>&1 && \
		for log in $(LOGS_DIR)/*.log; do \
			SIZE=$$(du -h "$$log" | cut -f1); \
			echo "               - $$(basename $$log) ($$SIZE)"; \
		done || echo "               (no log files yet)"; \
	else \
		echo "  Location:    Not created yet"; \
		echo "               Run 'make start-all' to create"; \
	fi
	@echo ""
	@echo "=========================================="

# =============================================================================
# 11. Troubleshooting & Utilities
# =============================================================================

# Clean everything (more aggressive than stop-all)
dev-clean:
	@echo "🧹 Cleaning up all processes and containers..."
	@-pkill -9 -f "uvicorn app.main:app" 2>/dev/null || true
	@-pkill -9 -f "celery -A app.core.queue" 2>/dev/null || true
	@-pkill -9 -f "npm run dev" 2>/dev/null || true
	@-pkill -9 -f "vite" 2>/dev/null || true
	@-pkill -9 -f "honcho" 2>/dev/null || true
	@-lsof -ti:8000 | xargs kill -9 2>/dev/null || true
	@-lsof -ti:5173 | xargs kill -9 2>/dev/null || true
	@docker compose down 2>/dev/null || true
	@docker compose -f docker-compose.test.yml down 2>/dev/null || true
	@sleep 0.5
	@echo "✓ Cleanup complete (including test databases)."

# Show which ports are in use
dev-ports:
	@echo "Port Status:"
	@echo ""
	@echo "PostgreSQL (5432):"
	@lsof -i :5432 2>/dev/null || echo "  ✗ Not in use"
	@echo ""
	@echo "Redis (6379):"
	@lsof -i :6379 2>/dev/null || echo "  ✗ Not in use"
	@echo ""
	@echo "Backend (8000):"
	@lsof -i :8000 2>/dev/null || echo "  ✗ Not in use"
	@echo ""
	@echo "Frontend (5173):"
	@lsof -i :5173 2>/dev/null || echo "  ✗ Not in use"

# Quick health check (fast alternative to dev-status)
dev-health:
	@echo "Quick Health Check:"
	@echo ""
	@printf "PostgreSQL:  "
	@docker ps 2>/dev/null | grep -q universalapi_postgres && echo "✓ Running" || echo "✗ Not running"
	@printf "Redis:       "
	@docker ps 2>/dev/null | grep -q universalapi_redis && echo "✓ Running" || echo "✗ Not running"
	@printf "Backend:     "
	@curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health --max-time 2 2>/dev/null | grep -q 200 && echo "✓ Running" || echo "✗ Not running"
	@printf "Frontend:    "
	@curl -s -o /dev/null -w "%{http_code}" http://localhost:5173 --max-time 2 2>/dev/null | grep -q 200 && echo "✓ Running" || echo "✗ Not running"
	@printf "Celery:      "
	@pgrep -f "celery.*worker" >/dev/null 2>&1 && echo "✓ Running" || echo "✗ Not running"

# =============================================================================
# Backward Compatibility Aliases (Deprecated)
# =============================================================================
# These aliases maintain backward compatibility with existing scripts.
# They will show deprecation warnings.
# =============================================================================

# Old → New mappings
start-local: app-start
	@echo "⚠️  'start-local' is deprecated. Use 'make app-start' or 'make start-all' instead."

restart-local: app-restart
	@echo "⚠️  'restart-local' is deprecated. Use 'make app-restart' or 'make restart-all' instead."

stop-local: app-stop
	@echo "⚠️  'stop-local' is deprecated. Use 'make app-stop' or 'make stop-all' instead."

local-status: status
	@echo "⚠️  'local-status' is deprecated. Use 'make status' instead."

logs-local: app-logs
	@echo "⚠️  'logs-local' is deprecated. Use 'make logs' or 'make app-logs' instead."

logs-all: logs
	@echo "⚠️  'logs-all' is deprecated. Use 'make logs' instead."

dev: infra-up
	@echo "⚠️  'dev' is deprecated. Use 'make infra-up' instead."

stop: infra-stop
	@echo "⚠️  'stop' is deprecated. Use 'make infra-stop' instead."

backend-run: backend-start
	@echo "⚠️  'backend-run' is deprecated. Use 'make backend-start' instead."

frontend-run: frontend-start
	@echo "⚠️  'frontend-run' is deprecated. Use 'make frontend-start' instead."

celery: celery-start
	@echo "⚠️  'celery' is deprecated. Use 'make celery-start' instead."

celery-beat:
	@echo "⚠️  'celery-beat' is deprecated. Use 'make celery-start' (starts both worker and beat) instead."
	@cd backend && poetry run celery -A app.core.queue.celery_app beat --loglevel=info

migrate: db-migrate
	@echo "⚠️  'migrate' is deprecated. Use 'make db-migrate' instead."

migrate-create: db-migrate-create
	@echo "⚠️  'migrate-create' is deprecated. Use 'make db-migrate-create' instead."

migrate-downgrade: db-migrate-rollback
	@echo "⚠️  'migrate-downgrade' is deprecated. Use 'make db-migrate-rollback' instead."

test: test-all
	@echo "⚠️  'test' is deprecated. Use 'make test-all' instead."

test-cov: test-with-coverage
	@echo "⚠️  'test-cov' is deprecated. Use 'make test-with-coverage' instead."

install: dev-install
	@echo "⚠️  'install' is deprecated. Use 'make dev-install' instead."

test-db-down: test-db-stop
	@echo "⚠️  'test-db-down' is deprecated. Use 'make test-db-stop' instead."

# Old component stop/restart aliases (for manual mode)
stop-app:
	@echo "⚠️  'stop-app' is deprecated. Use 'make app-stop' instead."
	@$(MAKE) app-stop

stop-backend:
	@echo "⚠️  'stop-backend' is deprecated. Use 'make backend-stop' instead."
	@$(MAKE) backend-stop

stop-frontend:
	@echo "⚠️  'stop-frontend' is deprecated. Use 'make frontend-stop' instead."
	@$(MAKE) frontend-stop

stop-celery:
	@echo "⚠️  'stop-celery' is deprecated. Use 'make celery-stop' instead."
	@$(MAKE) celery-stop

restart-app:
	@echo "⚠️  'restart-app' is deprecated and behaves differently now."
	@echo "    For Honcho mode: use 'make app-restart' or 'make restart-all'"
	@echo "    For Manual mode: use individual component restarts (backend-restart, frontend-restart, etc.)"
	@$(call check_infra_running)
	@mkdir -p $(LOGS_DIR)
	@-pkill -f "uvicorn app.main:app" 2>/dev/null || true
	@-pkill -f "celery -A app.core.queue" 2>/dev/null || true
	@-pkill -f "vite" 2>/dev/null || true
	@sleep 1
	@cd backend && poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 >> ../$(LOGS_DIR)/backend.log 2>&1 &
	@cd frontend && npm run dev >> ../$(LOGS_DIR)/frontend.log 2>&1 &
	@cd backend && poetry run celery -A app.core.queue.celery_app worker --loglevel=info >> ../$(LOGS_DIR)/celery_worker.log 2>&1 &
	@cd backend && poetry run celery -A app.core.queue.celery_app beat --loglevel=info >> ../$(LOGS_DIR)/celery_beat.log 2>&1 &
	@echo "App components restarted."

restart-backend:
	@echo "⚠️  'restart-backend' is deprecated. Use 'make backend-restart' instead."
	@$(MAKE) backend-restart

restart-frontend:
	@echo "⚠️  'restart-frontend' is deprecated. Use 'make frontend-restart' instead."
	@$(MAKE) frontend-restart

restart-celery:
	@echo "⚠️  'restart-celery' is deprecated. Use 'make celery-restart' instead."
	@$(MAKE) celery-restart

restart-docker:
	@echo "⚠️  'restart-docker' is deprecated. Use 'make infra-restart' instead."
	@$(MAKE) infra-restart

# Removed commands (show error messages)
db-up:
	@echo "❌ 'db-up' has been removed. Use 'make infra-up' instead."
	@exit 1

db-down:
	@echo "❌ 'db-down' has been removed. Use 'make infra-stop' instead."
	@exit 1

start:
	@echo "❌ 'start' (legacy) has been removed. Use 'make start-all' instead."
	@exit 1

test-plugins-e2e:
	@echo "⚠️  'test-plugins-e2e' is deprecated. Use 'make test-e2e' instead."
	@$(MAKE) test-e2e

dev-tools:
	@echo "⚠️  'dev-tools' is deprecated. Use 'make infra-up-tools' instead."
	@$(MAKE) infra-up-tools
