# CLAUDE.md — Project Context for AI Assistants

## Project Identity

**Name:** CodeLens AI
**Tagline:** AI-Powered Legacy Modernization Platform
**Description:** Helps engineering teams modernize legacy applications by analyzing
repositories, detecting technical debt, identifying outdated dependencies, and
generating AI-powered modernization recommendations.

**Target Users:** Enterprise engineering teams, CTOs, application modernization
teams, system integrators.

**Competition Context:** Built for the HyKr Build Challenge 2026.

---

## Repository Structure

```
legacy-modernization-platform/
├── frontend/          # Next.js 15 (App Router, TypeScript, Tailwind v4, shadcn/ui)
├── backend/           # FastAPI (Python 3.12+, SQLAlchemy 2.0, ARQ workers)
├── docs/              # Architecture, API, and development documentation
├── docker-compose.yml # PostgreSQL (pgvector), Redis, backend, worker, frontend
├── Makefile           # Development shortcuts
└── .github/workflows/ # CI/CD pipeline
```

---

## Tech Stack

### Frontend
- **Framework:** Next.js 15 with App Router
- **Language:** TypeScript (strict mode)
- **Styling:** Tailwind CSS v4 (CSS-first config, no tailwind.config.ts)
- **Components:** shadcn/ui (New York style) on Radix UI primitives
- **Auth:** Auth.js v5 (NextAuth) with GitHub OAuth provider
- **Charts:** Recharts
- **Icons:** Lucide React
- **Font:** Inter (Google Fonts via next/font)

### Backend
- **Framework:** FastAPI with async support
- **Language:** Python 3.12+
- **ORM:** SQLAlchemy 2.0 (async mode with asyncpg)
- **Validation:** Pydantic v2
- **Migrations:** Alembic
- **Queue:** ARQ (async Redis queue) — NOT Celery, NOT BullMQ
- **AST Parsing:** tree-sitter (Python bindings)
- **AI:** Anthropic Claude SDK + OpenAI SDK (provider-agnostic)
- **HTTP Client:** httpx (async)

### Infrastructure
- **Database:** PostgreSQL 16 with pgvector extension
- **Cache/Queue:** Redis 7
- **Containers:** Docker Compose
- **CI/CD:** GitHub Actions
- **Deployment:** Vercel (frontend) + Railway (backend)

---

## Architecture Principles

1. **Two-tier AI strategy:** 80% deterministic analysis (tree-sitter + rules = free),
   20% LLM-powered semantic analysis (Claude/OpenAI = paid). This keeps costs to
   $0.50-$5.00 per repository.

2. **Background processing:** All repo analysis runs as background jobs via ARQ
   workers. The frontend polls for progress. Never block the API.

3. **Service layer pattern:** API routes are thin controllers. All business logic
   lives in `backend/app/services/`. Routes call services, services call models.

4. **Server Components first:** Next.js pages are Server Components by default.
   Only use `"use client"` for interactive components (charts, forms, dropdowns).

5. **Modernization score:** Composite 0-100 score across 7 weighted dimensions:
   code_health (25%), dependency_health (20%), architecture_quality (15%),
   test_coverage (15%), documentation (10%), infrastructure_readiness (10%),
   security_posture (5%). Grades: A (80+), B (60-79), C (40-59), D (20-39), F (<20).

---

## Key Conventions

### Python (Backend)
- Use `async/await` for ALL I/O operations
- Type hints on every function signature
- Docstrings on every public class, function, and module
- PEP 8 via Ruff (max line length: 88)
- Import order: stdlib → third-party → local
- Use Pydantic v2 `.model_validate()` not `.from_orm()`
- Use SQLAlchemy 2.0 `select()` style, not legacy `query()`
- UUID primary keys everywhere (uuid-ossp extension)
- JSONB for flexible/variable-shape data columns
- Fernet encryption for GitHub tokens at rest

### TypeScript (Frontend)
- Strict mode — no `any` types
- JSDoc comments on all exported functions and components
- Server Components by default; `"use client"` only when needed
- Use `cn()` utility (clsx + tailwind-merge) for class merging
- Typed API client in `lib/api-client.ts` — never raw `fetch()`
- Color scheme: slate-950 bg, indigo/violet primary, cyan accent
- Dark mode first, light mode supported via CSS variables

### Database
- All tables use UUID primary keys (`uuid_generate_v4()`)
- Timestamps: `created_at` and `updated_at` on every table
- Foreign keys with `ON DELETE CASCADE`
- JSONB for arrays/objects: `issues`, `vulnerabilities`, `affected_files`
- pgvector for future semantic code search

### API
- RESTful, versioned: `/api/v1/*`
- JSON request/response bodies
- JWT auth via `Authorization: Bearer <token>` header
- Pagination: `?skip=0&limit=20`
- Consistent error format: `{"detail": "message", "status_code": 400}`

---

## File Naming

| Layer | Convention | Example |
|-------|-----------|---------|
| Python modules | snake_case | `ast_parser.py`, `debt_detector.py` |
| SQLAlchemy models | PascalCase class, snake_case file | `class Project` in `project.py` |
| Pydantic schemas | PascalCase with suffix | `ProjectCreate`, `ProjectResponse` |
| React components | PascalCase file + export | `ScoreGauge.tsx` or `score-gauge.tsx` |
| Next.js pages | `page.tsx` in route folder | `app/(dashboard)/projects/page.tsx` |
| CSS | kebab-case classes | `.score-gauge`, `.debt-table` |
| API routes | kebab-case URLs | `/api/v1/projects/:id/analysis/debt` |

---

## Analysis Pipeline Stages

```
1. Clone (0-15%)    → git clone --depth 1
2. Inventory (15-25%) → walk tree, detect languages, count LOC
3. AST Parse (25-45%) → tree-sitter: functions, classes, imports
4. Metrics (45-60%)   → complexity, nesting, coupling, debt rules
5. Dependencies (60-70%) → npm/PyPI registry lookups, CVE checks
6. AI Analysis (70-90%)  → Claude Haiku (bulk) + Sonnet (synthesis)
7. Scoring (90-100%)     → weighted composite → grade A-F
```

---

## Supported Languages (AST Parsing)

| Language | tree-sitter Grammar | Dependency Ecosystem |
|----------|-------------------|---------------------|
| Python | tree-sitter-python | pip (requirements.txt, pyproject.toml) |
| JavaScript | tree-sitter-javascript | npm (package.json) |
| TypeScript | tree-sitter-typescript | npm (package.json) |
| Java | tree-sitter-java | Maven (pom.xml) |

---

## Environment Variables

All config is in `.env` (see `.env.example`). Key variables:

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | PostgreSQL async connection string |
| `REDIS_URL` | Redis connection string |
| `GITHUB_CLIENT_ID/SECRET` | GitHub OAuth App credentials |
| `AUTH_SECRET` | JWT signing secret |
| `ANTHROPIC_API_KEY` | Claude API key |
| `OPENAI_API_KEY` | OpenAI API key (alternative) |
| `AI_PROVIDER` | `anthropic` or `openai` |
| `ENCRYPTION_KEY` | Fernet key for token encryption |

---

## Common Development Commands

```bash
make dev-backend       # Start FastAPI (port 8000)
make dev-frontend      # Start Next.js (port 3000)
make dev-worker        # Start ARQ background worker
make db-migrate        # Run Alembic migrations
make test              # Run all tests
make lint              # Lint Python + TypeScript
docker compose up -d postgres redis  # Start DB + Redis
```

---

## Testing Strategy

- **Backend:** pytest + pytest-asyncio for async tests
- **Frontend:** TypeScript compiler (`tsc --noEmit`) + ESLint + build verification
- **Integration:** Docker Compose with test database
- **E2E:** Manual verification against demo repos

---

## Debt Detection Rules (Built-in)

| ID | Category | Severity | Trigger |
|----|----------|----------|---------|
| COMPLEXITY_HIGH | complexity | high | Cyclomatic complexity > 10 |
| COMPLEXITY_CRITICAL | complexity | critical | Cyclomatic complexity > 20 |
| LONG_FUNCTION | complexity | medium | Function > 60 LOC |
| VERY_LONG_FUNCTION | complexity | high | Function > 150 LOC |
| DEEP_NESTING | complexity | medium | Nesting > 4 levels |
| TOO_MANY_PARAMS | style | medium | Parameters > 5 |
| GOD_CLASS | architecture | high | Class > 20 methods |
| LARGE_FILE | architecture | medium | File > 500 LOC |
| NO_DOCSTRING | documentation | low | Public function > 10 LOC, no docstring |
| HARDCODED_SECRET | security | critical | Regex match for API keys, passwords |
| SQL_INJECTION | security | critical | String concatenation in SQL |
| EVAL_USAGE | security | high | eval() or exec() calls |

---

## Important Files to Understand

| File | Purpose |
|------|---------|
| `backend/app/main.py` | FastAPI app factory, middleware, startup |
| `backend/app/core/config.py` | All configuration via Pydantic Settings |
| `backend/app/services/ast_parser.py` | tree-sitter multi-language parsing |
| `backend/app/services/scoring.py` | Modernization score algorithm |
| `backend/app/services/ai_pipeline.py` | Claude/OpenAI integration |
| `backend/app/workers/analysis_worker.py` | Background analysis pipeline |
| `frontend/src/lib/auth.ts` | Auth.js v5 configuration |
| `frontend/src/lib/api-client.ts` | Typed API client |
| `frontend/src/app/(dashboard)/layout.tsx` | Dashboard shell (sidebar + header) |
| `frontend/src/components/analysis/score-gauge.tsx` | Animated score visualization |

---

## Gotchas & Pitfalls

1. **tree-sitter grammars** require a C compiler. On Windows, install Visual Studio
   Build Tools. On Mac, `xcode-select --install`.

2. **Auth.js v5** is technically "beta" but production-ready. Use `next-auth@beta`.

3. **Tailwind CSS v4** uses CSS-first config (`@import "tailwindcss"` in globals.css),
   NOT a `tailwind.config.ts` file. The `tw-animate-css` package replaces
   `tailwindcss-animate`.

4. **SQLAlchemy async** requires `asyncpg` driver and `postgresql+asyncpg://` in the
   connection URL. The sync URL (for Alembic) uses plain `postgresql://`.

5. **ARQ** is the queue system — NOT Celery, NOT BullMQ. It's Python-native, async,
   and lightweight. Workers are started with `arq app.workers.worker_config.WorkerSettings`.

6. **GitHub OAuth `repo` scope** grants write access too. For MVP this is fine. In
   production, use GitHub Apps with fine-grained read-only permissions.

7. **pgvector** extension must be enabled before creating tables. The `init-db.sql`
   script handles this on first Docker container start.
