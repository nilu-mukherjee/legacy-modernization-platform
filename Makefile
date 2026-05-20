# =============================================================================
# CodeLens AI — Development Makefile
# =============================================================================
# Usage: make <target>
# Run `make help` to see all available commands.
# =============================================================================

.PHONY: help dev dev-frontend dev-backend dev-worker setup setup-frontend setup-backend db-up db-migrate db-reset docker-up docker-down test lint clean

# Default target
help: ## Show this help message
	@echo "CodeLens AI — Development Commands"
	@echo "=================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

setup: setup-backend setup-frontend ## Install all dependencies
	@echo "✅ All dependencies installed"

setup-frontend: ## Install frontend dependencies
	cd frontend && npm install

setup-backend: ## Install backend dependencies
	cd backend && pip install -r requirements.txt

# ---------------------------------------------------------------------------
# Development
# ---------------------------------------------------------------------------

dev: ## Start all services (Docker + frontend + backend)
	@echo "Starting Docker services..."
	docker compose up -d postgres redis
	@echo "Starting backend..."
	$(MAKE) dev-backend &
	@echo "Starting frontend..."
	$(MAKE) dev-frontend

dev-frontend: ## Start Next.js dev server (port 3000)
	cd frontend && npm run dev

dev-backend: ## Start FastAPI dev server (port 8000)
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-worker: ## Start ARQ background worker
	cd backend && arq app.workers.worker_config.WorkerSettings

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

db-up: ## Start PostgreSQL + Redis via Docker
	docker compose up -d postgres redis

db-migrate: ## Run Alembic database migrations
	cd backend && alembic upgrade head

db-reset: ## Reset database (drop + recreate + migrate)
	cd backend && alembic downgrade base && alembic upgrade head

db-seed: ## Seed demo data
	cd backend && python -m scripts.seed

# ---------------------------------------------------------------------------
# Docker
# ---------------------------------------------------------------------------

docker-up: ## Start all services via Docker Compose
	docker compose up -d

docker-down: ## Stop all Docker services
	docker compose down

docker-build: ## Build all Docker images
	docker compose build

docker-logs: ## Tail all Docker logs
	docker compose logs -f

# ---------------------------------------------------------------------------
# Testing
# ---------------------------------------------------------------------------

test: test-backend test-frontend ## Run all tests

test-backend: ## Run backend tests
	cd backend && python -m pytest tests/ -v --tb=short

test-frontend: ## Run frontend tests
	cd frontend && npm test

# ---------------------------------------------------------------------------
# Linting & Formatting
# ---------------------------------------------------------------------------

lint: lint-backend lint-frontend ## Lint all code

lint-backend: ## Lint Python code
	cd backend && python -m ruff check app/ --fix
	cd backend && python -m ruff format app/

lint-frontend: ## Lint TypeScript code
	cd frontend && npm run lint

# ---------------------------------------------------------------------------
# Cleanup
# ---------------------------------------------------------------------------

clean: ## Remove build artifacts and caches
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name node_modules -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .next -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleaned up"
