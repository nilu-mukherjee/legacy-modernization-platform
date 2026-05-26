# CodeLens AI

AI-powered legacy modernization platform. Connects to any GitHub repository, runs static analysis + LLM-powered review, and produces a scored modernization report with actionable recommendations.

**Live:** https://legacy-modernization-platform.vercel.app

---

## How It's Built

Analysis runs in two tiers to keep costs low:

- **80% deterministic** — tree-sitter AST parsing + rule-based debt detection (free, runs in-process)
- **20% AI-powered** — Claude Haiku for bulk file analysis, Sonnet for synthesis (~$0.50–$5.00 per repo)

All repo analysis runs as background jobs via ARQ workers. The API returns immediately with a job ID; the frontend polls for progress.

### Architecture

```
Browser
  └─▶ Next.js 15 (Vercel)
        └─▶ FastAPI (Railway)
              ├─▶ PostgreSQL (Neon)      — projects, analyses, debt items
              ├─▶ Redis (Upstash)        — ARQ job queue
              └─▶ ARQ Workers (Railway)
                    ├─▶ git clone --depth 1
                    ├─▶ tree-sitter AST parse
                    ├─▶ Debt rules engine
                    ├─▶ npm/PyPI/Maven registry lookups
                    └─▶ Claude API (Haiku + Sonnet)
```

### Analysis Pipeline

```
Clone (0–15%) → Inventory (15–25%) → AST Parse (25–45%) → Metrics (45–60%)
  → Dependencies (60–70%) → AI Analysis (70–90%) → Scoring (90–100%)
```

### Modernization Score

Composite 0–100 across 7 weighted dimensions → grade A–F.

| Dimension | Weight |
|-----------|--------|
| Code Health | 25% |
| Dependency Health | 20% |
| Architecture Quality | 15% |
| Test Coverage | 15% |
| Documentation | 10% |
| Infrastructure | 10% |
| Security | 5% |

---

## Tech Stack

### Frontend
| Technology | Purpose |
|-----------|---------|
| Next.js 15 (App Router) | React framework, Server Components |
| TypeScript strict | Type safety |
| Tailwind CSS v4 | CSS-first utility styling |
| shadcn/ui + Radix UI | Component primitives |
| Auth.js v5 | GitHub OAuth |
| Recharts | Score visualizations |
| jsPDF | Client-side PDF report export |

### Backend
| Technology | Purpose |
|-----------|---------|
| FastAPI | Async REST API |
| Python 3.12+ | Runtime |
| SQLAlchemy 2.0 async | ORM with asyncpg |
| Pydantic v2 | Schema validation |
| ARQ | Redis-backed background workers |
| tree-sitter | Multi-language AST parsing |
| Alembic | Database migrations |
| Anthropic SDK | Claude API integration |

### Infrastructure
| Technology | Purpose |
|-----------|---------|
| PostgreSQL 16 + pgvector | Primary database |
| Redis 7 | Job queue |
| Docker Compose | Local development |
| GitHub Actions | CI pipeline |

---

## Key Components

| File | Purpose |
|------|---------|
| `backend/app/workers/analysis_worker.py` | 7-stage analysis pipeline as ARQ background job |
| `backend/app/services/ast_parser.py` | tree-sitter parsing — Python, JS, TS, Java |
| `backend/app/services/scoring.py` | Weighted composite score algorithm |
| `backend/app/services/ai_pipeline.py` | Claude/OpenAI prompt management |
| `frontend/src/lib/api-client.ts` | Typed API client for all backend calls |
| `frontend/src/lib/download-report.ts` | Client-side PDF generation (jsPDF + IBM Plex) |
| `frontend/src/lib/auth.ts` | Auth.js v5 + backend token sync |

---

## Deployment

| Component | Service | Notes |
|-----------|---------|-------|
| Frontend | Vercel (free) | Auto-deploys from `main` |
| Backend + Worker | Railway | `start.sh` runs API + ARQ worker together |
| Database | Neon PostgreSQL | Free tier, pgvector enabled |
| Cache / Queue | Upstash Redis | Free tier |

**~$5/mo total** (Railway hobby plan only paid component).

---

## Setup

### Prerequisites

- Node.js 20+, Python 3.12+, Docker & Docker Compose
- GitHub OAuth App ([create](https://github.com/settings/developers))
- Anthropic API key (or OpenAI)

### 1. Clone & configure

```bash
git clone https://github.com/nilu-mukherjee/legacy-modernization-platform.git
cd legacy-modernization-platform
cp .env.example .env
```

Key `.env` values to fill in:

```env
GITHUB_CLIENT_ID=...
GITHUB_CLIENT_SECRET=...
AUTH_SECRET=<openssl rand -base64 32>
NEXTAUTH_URL=http://localhost:3000
ANTHROPIC_API_KEY=...
AI_PROVIDER=anthropic
ENCRYPTION_KEY=<python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())">
DATABASE_URL=postgresql+asyncpg://codelens:codelens@localhost:5432/codelens
REDIS_URL=redis://localhost:6379
```

### 2. Start infrastructure

```bash
docker compose up -d postgres redis
```

### 3. Backend

```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
```

### 4. Frontend

```bash
cd frontend
npm install
```

### 5. Run

```bash
make dev-backend   # Terminal 1 — FastAPI on :8000
make dev-worker    # Terminal 2 — ARQ background worker
make dev-frontend  # Terminal 3 — Next.js on :3000
```

Open http://localhost:3000 and sign in with GitHub.

### Docker (all-in-one)

```bash
docker compose up -d
```

---

## Supported Languages

| Language | AST Parsing | Dependency Analysis |
|----------|:-----------:|:-------------------:|
| Python | ✅ | ✅ pip |
| JavaScript | ✅ | ✅ npm |
| TypeScript | ✅ | ✅ npm |
| Java | ✅ | ✅ Maven |

---

## License

MIT — see [LICENSE](LICENSE).
