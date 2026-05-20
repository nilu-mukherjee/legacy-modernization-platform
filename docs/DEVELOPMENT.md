# =============================================================================
# CodeLens AI — Development Guide
# =============================================================================
# Step-by-step guide for setting up the development environment and
# contributing to the project.
# =============================================================================

# Development Guide

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Setup](#environment-setup)
3. [GitHub OAuth Setup](#github-oauth-setup)
4. [Database Setup](#database-setup)
5. [Backend Development](#backend-development)
6. [Frontend Development](#frontend-development)
7. [Running the Full Stack](#running-the-full-stack)
8. [Testing](#testing)
9. [Code Style](#code-style)
10. [Database Migrations](#database-migrations)
11. [Adding New Features](#adding-new-features)
12. [Debugging Tips](#debugging-tips)
13. [Common Issues](#common-issues)

---

## Prerequisites

Ensure you have the following installed:

| Tool | Version | Installation |
|------|---------|-------------|
| **Node.js** | 20+ | [nodejs.org](https://nodejs.org/) |
| **Python** | 3.12+ | [python.org](https://python.org/) |
| **Docker** | 24+ | [docker.com](https://docker.com/) |
| **Docker Compose** | 2.20+ | Included with Docker Desktop |
| **Git** | 2.40+ | [git-scm.com](https://git-scm.com/) |

Optional but recommended:
- **Make** — for running Makefile commands (Windows: install via `choco install make`)
- **VS Code** — with Python and TypeScript extensions

---

## Environment Setup

### 1. Clone the repository

```bash
git clone https://github.com/your-username/legacy-modernization-platform.git
cd legacy-modernization-platform
```

### 2. Create environment file

```bash
cp .env.example .env
```

### 3. Generate secrets

```bash
# Generate AUTH_SECRET
openssl rand -base64 32
# OR: python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate ENCRYPTION_KEY
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 4. Fill in .env

Edit `.env` with:
- Your GitHub OAuth credentials (see next section)
- Generated secrets from above
- AI provider API key (Anthropic or OpenAI)

---

## GitHub OAuth Setup

1. Go to [GitHub Developer Settings](https://github.com/settings/developers)
2. Click "New OAuth App"
3. Fill in:
   - **Application name**: CodeLens AI (Dev)
   - **Homepage URL**: `http://localhost:3000`
   - **Authorization callback URL**: `http://localhost:3000/api/auth/callback/github`
4. Click "Register application"
5. Copy the **Client ID** → `GITHUB_CLIENT_ID` in `.env`
6. Generate a **Client Secret** → `GITHUB_CLIENT_SECRET` in `.env`

> **Important**: The callback URL must match exactly. For production, create
> a separate OAuth App with the production URL.

---

## Database Setup

### Start PostgreSQL and Redis

```bash
docker compose up -d postgres redis
```

This starts:
- **PostgreSQL** on port 5432 (with pgvector extension)
- **Redis** on port 6379

### Verify containers are running

```bash
docker compose ps
# Both should show "healthy" status
```

### Run database migrations

```bash
cd backend
pip install -r requirements.txt  # Install dependencies first
alembic upgrade head             # Apply all migrations
```

### Connect to database (optional)

```bash
# Via psql
docker compose exec postgres psql -U codelens -d codelens

# Via pgAdmin or DBeaver
# Host: localhost, Port: 5432, User: codelens, Password: codelens, Database: codelens
```

---

## Backend Development

### Install dependencies

```bash
cd backend
python -m venv .venv                # Create virtual environment
source .venv/bin/activate           # Linux/Mac
# .venv\Scripts\activate            # Windows
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Dev tools (pytest, ruff, mypy)
```

### Start the API server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Start the background worker

```bash
# In a separate terminal
arq app.workers.worker_config.WorkerSettings
```

### Project structure

```
backend/
├── app/
│   ├── api/v1/routes/    # HTTP endpoints (thin layer)
│   ├── core/             # Configuration, database, security
│   ├── models/           # SQLAlchemy ORM models
│   ├── schemas/          # Pydantic request/response models
│   ├── services/         # Business logic (the "meat")
│   └── workers/          # Background job definitions
├── alembic/              # Database migrations
├── scripts/              # Utility scripts
└── tests/                # Test suite
```

### Key conventions

- **Routes** are thin — they validate input, call services, return responses
- **Services** contain all business logic
- **Models** are pure data — no business logic
- **Schemas** are Pydantic models for API contracts

---

## Frontend Development

### Install dependencies

```bash
cd frontend
npm install
```

### Start the dev server

```bash
npm run dev
```

The app will be available at http://localhost:3000.

### Project structure

```
frontend/src/
├── app/                      # Next.js App Router
│   ├── (marketing)/          # Public pages (landing)
│   ├── (auth)/               # Login/signup pages
│   ├── (dashboard)/          # Protected dashboard pages
│   └── api/auth/             # Auth.js route handlers
├── components/
│   ├── ui/                   # shadcn/ui primitives
│   ├── dashboard/            # Dashboard-specific components
│   ├── analysis/             # Analysis visualization components
│   └── shared/               # Shared utilities (loading, errors)
├── lib/                      # Utilities, API client, auth config
├── hooks/                    # Custom React hooks
└── types/                    # TypeScript type definitions
```

### Key conventions

- **Server Components** by default — only use `"use client"` when needed
- **Collocate** types with their components when possible
- **API calls** go through the typed API client (`lib/api-client.ts`)

---

## Running the Full Stack

### Option 1: Makefile (Recommended)

```bash
# Start infrastructure
docker compose up -d postgres redis

# In separate terminals:
make dev-backend      # Terminal 1: API server
make dev-worker       # Terminal 2: Background worker
make dev-frontend     # Terminal 3: Next.js dev server
```

### Option 2: Docker Compose (Everything)

```bash
docker compose up -d
```

### Verify everything works

1. Open http://localhost:3000 — Landing page
2. Click "Sign in with GitHub" — OAuth flow
3. After login, you should see the dashboard
4. The API docs are at http://localhost:8000/docs

---

## Testing

### Backend tests

```bash
cd backend

# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ -v --cov=app --cov-report=html

# Run specific test file
python -m pytest tests/test_scoring.py -v

# Run tests matching a pattern
python -m pytest tests/ -k "test_complexity" -v
```

### Frontend tests

```bash
cd frontend

# Type checking
npx tsc --noEmit

# Lint
npm run lint

# Build (catches errors)
npm run build
```

---

## Code Style

### Backend (Python)

We use **Ruff** for both linting and formatting:

```bash
cd backend

# Lint (check)
python -m ruff check app/

# Lint (fix)
python -m ruff check app/ --fix

# Format
python -m ruff format app/

# Type check
python -m mypy app/ --ignore-missing-imports
```

Style rules:
- PEP 8 compliance
- Type hints on all functions
- Docstrings on all public classes and functions
- Max line length: 88 (Black-compatible)
- Import sorting: isort-compatible

### Frontend (TypeScript)

We use **ESLint** with Next.js config:

```bash
cd frontend

# Lint
npm run lint

# Type check
npx tsc --noEmit
```

Style rules:
- TypeScript strict mode
- No `any` types
- JSDoc on all exports
- React Server Components by default

---

## Database Migrations

### Create a new migration

```bash
cd backend

# After modifying SQLAlchemy models:
alembic revision --autogenerate -m "description of change"
```

### Apply migrations

```bash
alembic upgrade head      # Apply all pending migrations
alembic upgrade +1        # Apply next migration
```

### Rollback migrations

```bash
alembic downgrade -1      # Rollback last migration
alembic downgrade base    # Rollback all migrations
```

### View migration history

```bash
alembic history --verbose
alembic current           # Show current revision
```

---

## Adding New Features

### Adding a new API endpoint

1. **Model**: Add/modify SQLAlchemy model in `app/models/`
2. **Schema**: Add Pydantic schemas in `app/schemas/`
3. **Migration**: Generate Alembic migration
4. **Service**: Implement business logic in `app/services/`
5. **Route**: Add endpoint in `app/api/v1/routes/`
6. **Register**: Include router in `app/api/v1/router.py`
7. **Test**: Add tests in `tests/`

### Adding a new frontend page

1. **Type**: Add TypeScript interfaces in `src/types/`
2. **API Client**: Add methods to `src/lib/api-client.ts`
3. **Page**: Create page in `src/app/(dashboard)/`
4. **Components**: Build components in `src/components/`
5. **Hook**: Add data-fetching hook if needed in `src/hooks/`
6. **Navigation**: Add link to sidebar in `src/components/dashboard/sidebar.tsx`

### Adding a new analysis rule

1. Add the rule to `DEBT_RULES` in `app/services/debt_detector.py`
2. Define: category, severity, check function, title template, suggestion
3. Add tests in `tests/test_debt_detector.py`

---

## Debugging Tips

### Backend

```python
# FastAPI auto-reloads on file changes when using --reload

# View SQL queries (add to config.py):
# import logging
# logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# Debug with breakpoint:
# import pdb; pdb.set_trace()
# Or: breakpoint()
```

### Frontend

```typescript
// Next.js hot-reloads automatically

// Debug server components:
console.log('Server:', data)  // Appears in terminal

// Debug client components:
console.log('Client:', data)  // Appears in browser console
```

### Database

```sql
-- Connect to database
docker compose exec postgres psql -U codelens -d codelens

-- View tables
\dt

-- View table schema
\d+ projects

-- Count records
SELECT COUNT(*) FROM projects;
SELECT COUNT(*) FROM analyses;
```

### Redis

```bash
# Connect to Redis
docker compose exec redis redis-cli

# View all keys
KEYS *

# View job queue
KEYS arq:*

# View job data
HGETALL job:<job-id>
```

---

## Common Issues

### "CORS error" in browser

Ensure `CORS_ORIGINS` in `.env` includes `http://localhost:3000`.

### "Connection refused" to PostgreSQL

```bash
# Check if container is running
docker compose ps postgres

# Restart if needed
docker compose restart postgres
```

### "Module not found" in Python

```bash
# Make sure you're in the virtual environment
source backend/.venv/bin/activate  # Linux/Mac
# backend\.venv\Scripts\activate   # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### "Alembic migration failed"

```bash
# Check current revision
cd backend && alembic current

# If out of sync, reset:
alembic downgrade base
alembic upgrade head
```

### "GitHub OAuth callback error"

Verify your OAuth App settings:
- Callback URL must be exactly: `http://localhost:3000/api/auth/callback/github`
- Client ID and Secret match your `.env` file

### "tree-sitter build failed"

tree-sitter grammars require a C compiler:
- **Windows**: Install Visual Studio Build Tools
- **Linux**: `apt install build-essential`
- **Mac**: `xcode-select --install`
