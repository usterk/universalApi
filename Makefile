.PHONY: help dev dev-tools stop logs db-up db-down migrate migrate-create test lint format install backend-install frontend-install celery

# Default target
help:
	@echo "UniversalAPI - Available commands:"
	@echo ""
	@echo "  Development:"
	@echo "    make dev           - Start development environment (PostgreSQL + Redis)"
	@echo "    make dev-tools     - Start with pgAdmin and Redis Commander"
	@echo "    make stop          - Stop all containers"
	@echo "    make logs          - Show container logs"
	@echo ""
	@echo "  Backend:"
	@echo "    make backend-install  - Install backend dependencies"
	@echo "    make backend-run      - Run FastAPI development server"
	@echo "    make celery           - Run Celery worker"
	@echo "    make migrate          - Run database migrations"
	@echo "    make migrate-create   - Create new migration (NAME=migration_name)"
	@echo ""
	@echo "  Frontend:"
	@echo "    make frontend-install - Install frontend dependencies"
	@echo "    make frontend-run     - Run Vite development server"
	@echo ""
	@echo "  Quality:"
	@echo "    make test          - Run tests"
	@echo "    make lint          - Run linters"
	@echo "    make format        - Format code"

# Development environment
dev:
	docker-compose up -d

dev-tools:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml --profile tools up -d

stop:
	docker-compose down

logs:
	docker-compose logs -f

# Database
db-up:
	docker-compose up -d postgres redis

db-down:
	docker-compose down

# Backend
backend-install:
	cd backend && poetry install

backend-run:
	cd backend && poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

celery:
	cd backend && poetry run celery -A app.core.queue.celery_app worker --loglevel=info

celery-beat:
	cd backend && poetry run celery -A app.core.queue.celery_app beat --loglevel=info

# Migrations
migrate:
	cd backend && poetry run alembic upgrade head

migrate-create:
	cd backend && poetry run alembic revision --autogenerate -m "$(NAME)"

migrate-downgrade:
	cd backend && poetry run alembic downgrade -1

# Frontend
frontend-install:
	cd frontend && npm install

frontend-run:
	cd frontend && npm run dev

# Testing
test:
	cd backend && poetry run pytest

test-cov:
	cd backend && poetry run pytest --cov=app --cov-report=html

# Code quality
lint:
	cd backend && poetry run ruff check .
	cd frontend && npm run lint

format:
	cd backend && poetry run ruff format .
	cd frontend && npm run format

# Full install
install: backend-install frontend-install
	@echo "All dependencies installed!"

# Quick start
start: dev backend-run
