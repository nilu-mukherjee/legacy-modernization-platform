<p align="center">
  <h1 align="center">🔬 CodeLens AI</h1>
  <p align="center">
    <strong>AI-Powered Legacy Modernization Platform</strong>
  </p>
  <p align="center">
    Analyze. Understand. Modernize.
  </p>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#getting-started">Getting Started</a> •
  <a href="#api-reference">API Reference</a> •
  <a href="#tech-stack">Tech Stack</a> •
  <a href="#deployment">Deployment</a>
</p>

---

## Overview

**CodeLens AI** helps engineering teams modernize legacy applications faster by analyzing repositories, detecting technical debt, identifying outdated dependencies, and generating AI-powered modernization recommendations.

Turn weeks of manual codebase assessment into minutes of automated intelligence.

### Why CodeLens AI?

| Problem | Solution |
|---------|----------|
| Manual code audits take weeks | Automated analysis in minutes |
| Technical debt is invisible | Quantified with severity scoring |
| Dependency risks are hidden | CVE detection + version tracking |
| Modernization planning is ad-hoc | AI-generated prioritized roadmaps |
| No single source of truth | Unified modernization dashboard |

---

## Features

### Core Capabilities

- **🔗 GitHub Repository Ingestion** — Connect any GitHub repo (public or private) via OAuth
- **🌳 Repository Structure Visualization** — Interactive file tree with language detection
- **📊 Technical Debt Analysis** — Rule-based + AI-powered debt detection across 6 categories
- **📦 Dependency Risk Detection** — Version lag, CVE scanning, deprecation alerts
- **🤖 AI-Generated Recommendations** — Prioritized modernization steps with effort estimates
- **💡 AI-Assisted Refactoring** — On-demand code refactoring suggestions with before/after diffs
- **🎯 Modernization Readiness Score** — 0-100 composite score across 7 dimensions
- **📈 Dashboard & Reports** — Real-time insights, charts, and exportable reports
- **🔐 GitHub OAuth Authentication** — Secure sign-in with fine-grained repo access
- **📋 Project Management** — Track multiple repositories and their modernization progress

### Analysis Dimensions

| Dimension | Weight | Metrics |
|-----------|--------|---------|
| Code Health | 25% | Cyclomatic complexity, function length, nesting depth |
| Dependency Health | 20% | Outdated packages, CVEs, deprecated libraries |
| Architecture Quality | 15% | Coupling, circular dependencies, module cohesion |
| Test Coverage | 15% | Test file presence, test-to-source ratio |
| Documentation | 10% | README quality, comment density |
| Infrastructure | 10% | Dockerfile, CI/CD config, env setup |
| Security | 5% | Hardcoded secrets, known vulnerabilities |

### Supported Languages

| Language | AST Parsing | Dependency Analysis | AI Analysis |
|----------|:-----------:|:-------------------:|:-----------:|
| JavaScript | ✅ | ✅ (npm) | ✅ |
| TypeScript | ✅ | ✅ (npm) | ✅ |
| Python | ✅ | ✅ (pip) | ✅ |
| Java | ✅ | ✅ (Maven) | ✅ |
| Go | 🔜 | 🔜 | ✅ |
| Ruby | 🔜 | 🔜 | ✅ |

---

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    CodeLens AI Platform                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────────┐ │
│  │  Next.js 15   │   │   FastAPI     │   │  ARQ Workers     │ │
│  │  Frontend     │──▶│   Backend     │──▶│  (Background)    │ │
│  │  (Port 3000)  │   │  (Port 8000)  │   │                  │ │
│  └──────────────┘   └──────┬───────┘   └────────┬─────────┘ │
│                             │                     │           │
│                      ┌──────┴───────┐      ┌─────┴─────┐    │
│                      │  PostgreSQL   │      │   Redis    │    │
│                      │  + pgvector   │      │  (Queue)   │    │
│                      └──────────────┘      └───────────┘    │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│  External Services:  GitHub API  │  Claude/OpenAI  │  npm/PyPI │
└─────────────────────────────────────────────────────────────┘
```

### Analysis Pipeline

```
User submits repo → Clone → Parse (tree-sitter) → Metrics → AI Analysis → Score → Dashboard
```

### Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Backend | FastAPI (Python) | Superior AST/ML ecosystem, async support |
| Frontend | Next.js 15 (App Router) | Server components, optimal DX |
| Queue | ARQ (async Redis queue) | Lightweight, perfect for MVP |
| Database | PostgreSQL + pgvector | Relational + vector search in one DB |
| AST Parser | tree-sitter | Multi-language, production-proven (VS Code, GitHub) |
| AI | Claude + OpenAI (pluggable) | Haiku for bulk, Sonnet for synthesis |

---

## Getting Started

### Prerequisites

- **Node.js** 20+ ([Download](https://nodejs.org/))
- **Python** 3.12+ ([Download](https://python.org/))
- **Docker** & Docker Compose ([Download](https://docker.com/))
- **Git** ([Download](https://git-scm.com/))
- **GitHub OAuth App** ([Create one](https://github.com/settings/developers))

### Quick Start

#### 1. Clone the repository

```bash
git clone https://github.com/your-username/legacy-modernization-platform.git
cd legacy-modernization-platform
```

#### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your API keys and OAuth credentials
```

Required environment variables:
- `GITHUB_CLIENT_ID` / `GITHUB_CLIENT_SECRET` — [Create GitHub OAuth App](https://github.com/settings/developers)
- `AUTH_SECRET` — Generate with: `openssl rand -base64 32`
- `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` — For AI-powered analysis
- `ENCRYPTION_KEY` — Generate with: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`

#### 3. Start infrastructure

```bash
# Start PostgreSQL + Redis
docker compose up -d postgres redis
```

#### 4. Setup backend

```bash
cd backend
pip install -r requirements.txt
alembic upgrade head     # Run database migrations
cd ..
```

#### 5. Setup frontend

```bash
cd frontend
npm install
cd ..
```

#### 6. Start development servers

```bash
# Terminal 1: Backend API
make dev-backend

# Terminal 2: Background worker
make dev-worker

# Terminal 3: Frontend
make dev-frontend
```

#### 7. Open the app

Navigate to [http://localhost:3000](http://localhost:3000) and sign in with GitHub.

### Using Docker (Alternative)

```bash
# Start everything with Docker Compose
docker compose up -d

# View logs
docker compose logs -f
```

---

## Project Structure

```
legacy-modernization-platform/
├── frontend/                    # Next.js 15 App (TypeScript)
│   ├── src/
│   │   ├── app/                # App Router pages
│   │   │   ├── (marketing)/    # Landing page
│   │   │   ├── (auth)/         # Login/signup
│   │   │   └── (dashboard)/    # Protected dashboard
│   │   ├── components/
│   │   │   ├── ui/             # shadcn/ui primitives
│   │   │   ├── dashboard/      # Dashboard components
│   │   │   ├── analysis/       # Analysis visualizations
│   │   │   └── shared/         # Shared components
│   │   ├── lib/                # Utilities, API client
│   │   ├── hooks/              # Custom React hooks
│   │   └── types/              # TypeScript types
│   └── package.json
│
├── backend/                     # FastAPI Backend (Python)
│   ├── app/
│   │   ├── api/v1/routes/      # API endpoints
│   │   ├── core/               # Config, database, security
│   │   ├── models/             # SQLAlchemy ORM models
│   │   ├── schemas/            # Pydantic schemas
│   │   ├── services/           # Business logic
│   │   └── workers/            # Background job workers
│   ├── alembic/                # Database migrations
│   └── requirements.txt
│
├── docker-compose.yml           # Infrastructure orchestration
├── Makefile                     # Development shortcuts
├── .env.example                 # Environment template
└── .github/workflows/ci.yml    # CI/CD pipeline
```

---

## API Reference

### Base URL

```
http://localhost:8000/api/v1
```

### Authentication

All endpoints (except `/health` and `/auth/sync`) require a valid JWT token in the `Authorization: Bearer <token>` header.

### Endpoints

#### Health Check

```http
GET /health
```

#### Authentication

```http
POST /api/v1/auth/sync          # Sync user from GitHub OAuth
GET  /api/v1/auth/me            # Get current user profile
```

#### Projects

```http
GET    /api/v1/projects                    # List user's projects
POST   /api/v1/projects                    # Create project + trigger analysis
GET    /api/v1/projects/:id                # Get project details
DELETE /api/v1/projects/:id                # Delete project
POST   /api/v1/projects/:id/analyze        # Re-trigger analysis
```

#### Analysis

```http
GET /api/v1/projects/:id/analysis              # Latest analysis summary
GET /api/v1/projects/:id/analysis/score        # Modernization readiness score
GET /api/v1/projects/:id/analysis/files        # File-level metrics (paginated)
GET /api/v1/projects/:id/analysis/debt         # Technical debt items
GET /api/v1/projects/:id/analysis/dependencies # Dependency health
GET /api/v1/projects/:id/analysis/structure    # Repository file tree
```

#### AI Recommendations

```http
GET  /api/v1/projects/:id/recommendations              # All recommendations
GET  /api/v1/projects/:id/recommendations/:rec_id       # Single recommendation
POST /api/v1/projects/:id/recommendations/:rec_id/refactor  # Generate refactored code
```

#### Reports

```http
GET /api/v1/projects/:id/report              # Full report data
GET /api/v1/projects/:id/report/export       # Export (format=json)
```

#### Jobs

```http
GET /api/v1/jobs/:id                    # Job status + progress
GET /api/v1/projects/:id/jobs           # All jobs for a project
```

### Example: Create & Analyze a Project

```bash
# 1. Create project
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"repo_url": "https://github.com/user/repo", "name": "My Legacy App"}'

# Response: { "id": "uuid", "status": "analyzing", "job_id": "uuid" }

# 2. Poll job status
curl http://localhost:8000/api/v1/jobs/<job_id> \
  -H "Authorization: Bearer <token>"

# Response: { "progress": 65, "current_step": "AI analysis in progress" }

# 3. Get results
curl http://localhost:8000/api/v1/projects/<id>/analysis/score \
  -H "Authorization: Bearer <token>"

# Response: { "overall_score": 42.5, "grade": "C", "sub_scores": {...} }
```

---

## Tech Stack

### Frontend

| Technology | Version | Purpose |
|-----------|---------|---------|
| [Next.js](https://nextjs.org/) | 15.x | React framework (App Router) |
| [React](https://react.dev/) | 19.x | UI library |
| [TypeScript](https://typescriptlang.org/) | 5.x | Type safety |
| [Tailwind CSS](https://tailwindcss.com/) | 4.x | Utility-first CSS |
| [shadcn/ui](https://ui.shadcn.com/) | latest | Component library |
| [Recharts](https://recharts.org/) | 2.x | Data visualization |
| [Auth.js](https://authjs.dev/) | 5.x | Authentication |
| [Lucide React](https://lucide.dev/) | latest | Icon library |

### Backend

| Technology | Version | Purpose |
|-----------|---------|---------|
| [FastAPI](https://fastapi.tiangolo.com/) | 0.115.x | API framework |
| [Python](https://python.org/) | 3.12+ | Runtime |
| [SQLAlchemy](https://sqlalchemy.org/) | 2.0.x | ORM (async) |
| [Pydantic](https://pydantic.dev/) | 2.x | Data validation |
| [ARQ](https://arq-docs.helpmanual.io/) | 0.26.x | Background jobs |
| [tree-sitter](https://tree-sitter.github.io/) | 0.23.x | AST parsing |
| [Alembic](https://alembic.sqlalchemy.org/) | 1.13.x | Migrations |

### Infrastructure

| Technology | Purpose |
|-----------|---------|
| [PostgreSQL](https://postgresql.org/) + [pgvector](https://github.com/pgvector/pgvector) | Database + vector search |
| [Redis](https://redis.io/) | Job queue + cache |
| [Docker](https://docker.com/) | Containerization |
| [GitHub Actions](https://github.com/features/actions) | CI/CD |

### AI/Analysis

| Technology | Purpose |
|-----------|---------|
| [Claude](https://anthropic.com/) (Anthropic) | Code analysis + recommendations |
| [OpenAI](https://openai.com/) | Alternative AI provider |
| [tree-sitter](https://tree-sitter.github.io/) | Multi-language AST parsing |

---

## Deployment

### MVP Deployment (Recommended)

| Component | Service | Cost |
|-----------|---------|------|
| Frontend | [Vercel](https://vercel.com/) (Free) | $0/mo |
| Backend + Worker | [Railway](https://railway.app/) ($5) | ~$5/mo |
| PostgreSQL | [Neon](https://neon.tech/) (Free) | $0/mo |
| Redis | [Upstash](https://upstash.com/) (Free) | $0/mo |
| **Total** | | **~$5/mo** |

### Production Deployment

For production workloads, deploy on AWS with:
- ECS (Fargate) for containers
- RDS for PostgreSQL
- ElastiCache for Redis
- S3 for temporary repo storage
- CloudWatch for monitoring

---

## Development

### Available Commands

```bash
make help              # Show all commands
make setup             # Install all dependencies
make dev               # Start all services
make dev-frontend      # Start frontend only
make dev-backend       # Start backend only
make dev-worker        # Start background worker
make test              # Run all tests
make lint              # Lint all code
make db-migrate        # Run database migrations
make db-reset          # Reset database
make docker-up         # Start via Docker Compose
```

### Environment Variables

See [.env.example](.env.example) for all configuration options.

---

## Modernization Scoring

### Score Grades

| Grade | Score | Meaning | Color |
|-------|-------|---------|-------|
| **A** | 80-100 | Modernization Ready | 🟢 Green |
| **B** | 60-79 | Good Foundation | 🟢 Lime |
| **C** | 40-59 | Needs Attention | 🟡 Yellow |
| **D** | 20-39 | Significant Debt | 🟠 Orange |
| **F** | 0-19 | Critical Modernization Needed | 🔴 Red |

### Technical Debt Categories

- **Complexity** — High cyclomatic complexity, deep nesting, long functions
- **Architecture** — God classes, circular dependencies, tight coupling
- **Style** — Too many parameters, inconsistent naming, missing types
- **Security** — Hardcoded secrets, SQL injection, eval() usage
- **Documentation** — Missing docstrings, no README, low comment ratio
- **Duplication** — Repeated code patterns, copy-paste smells

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- [tree-sitter](https://tree-sitter.github.io/) for multi-language AST parsing
- [shadcn/ui](https://ui.shadcn.com/) for beautiful UI components
- [Anthropic Claude](https://anthropic.com/) for AI-powered code analysis
- [pgvector](https://github.com/pgvector/pgvector) for vector similarity search

---

<p align="center">
  Built with ❤️ for the HyKr Build Challenge 2026
</p>