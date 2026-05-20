# =============================================================================
# CodeLens AI — Architecture Documentation
# =============================================================================
# This document provides a deep-dive into the system architecture, design
# decisions, data flow, and component interactions.
# =============================================================================

# Architecture Guide

## Table of Contents

1. [System Overview](#system-overview)
2. [Component Architecture](#component-architecture)
3. [Data Flow](#data-flow)
4. [Repository Analysis Pipeline](#repository-analysis-pipeline)
5. [AI Pipeline](#ai-pipeline)
6. [Database Design](#database-design)
7. [Authentication Flow](#authentication-flow)
8. [Background Job System](#background-job-system)
9. [Security Architecture](#security-architecture)
10. [Scalability Considerations](#scalability-considerations)

---

## System Overview

CodeLens AI follows a **three-tier architecture** with clear separation of concerns:

```
┌────────────────────────────────────────────────────────────────┐
│                         Presentation Tier                       │
│                                                                  │
│  Next.js 15 (App Router)                                        │
│  ├── Server Components (SSR, data fetching)                     │
│  ├── Client Components (interactivity, charts)                  │
│  ├── Auth.js v5 (GitHub OAuth)                                  │
│  └── API Routes (BFF proxy to backend)                          │
├────────────────────────────────────────────────────────────────┤
│                         Application Tier                        │
│                                                                  │
│  FastAPI (Python 3.12+)                                         │
│  ├── REST API (versioned: /api/v1/*)                            │
│  ├── Service Layer (business logic)                             │
│  ├── ARQ Workers (background processing)                        │
│  └── AI Pipeline (Claude/OpenAI integration)                    │
├────────────────────────────────────────────────────────────────┤
│                           Data Tier                             │
│                                                                  │
│  PostgreSQL + pgvector (persistent storage)                     │
│  Redis (job queue + cache + session)                            │
│  Filesystem (temporary repo clones)                             │
└────────────────────────────────────────────────────────────────┘
```

---

## Component Architecture

### Frontend Components

```
Next.js 15 Application
├── Marketing Pages (SSR, public)
│   └── Landing page, features, pricing
├── Auth Pages (SSR, public)
│   └── GitHub OAuth login flow
├── Dashboard (SSR + CSR, protected)
│   ├── Overview — aggregate stats, recent projects
│   ├── Projects — CRUD, project cards
│   └── Project Detail
│       ├── Score Gauge — animated modernization score
│       ├── Radar Chart — sub-score breakdown
│       ├── Debt Table — sortable technical debt items
│       ├── Dependency Table — package risk matrix
│       ├── Recommendation Cards — AI-generated insights
│       ├── File Tree — repository structure visualization
│       └── Report Export — JSON/PDF generation
└── Shared UI
    ├── shadcn/ui primitives (Button, Card, Badge, etc.)
    ├── Loading skeletons
    ├── Error boundaries
    └── Empty states
```

### Backend Components

```
FastAPI Application
├── API Layer
│   ├── Auth routes (/auth/*)
│   ├── Project routes (/projects/*)
│   ├── Analysis routes (/projects/:id/analysis/*)
│   ├── Recommendation routes (/projects/:id/recommendations/*)
│   ├── Report routes (/projects/:id/report/*)
│   └── Job routes (/jobs/*)
├── Service Layer
│   ├── IngestionService — repo cloning, file inventory
│   ├── ASTParserService — tree-sitter multi-language parsing
│   ├── MetricsService — complexity, LOC, coupling computation
│   ├── DebtDetectorService — rule-based debt detection
│   ├── DependencyAnalyzerService — package version/CVE checking
│   ├── AIPipelineService — LLM integration (Claude/OpenAI)
│   ├── ScoringService — modernization score calculation
│   └── ReportGeneratorService — report assembly + export
├── Worker Layer
│   └── AnalysisWorker — orchestrates full pipeline
└── Core
    ├── Config — Pydantic Settings
    ├── Database — async SQLAlchemy
    ├── Redis — async Redis client
    └── Security — JWT, encryption
```

---

## Data Flow

### Project Creation & Analysis Flow

```
1. User clicks "Analyze Repository" in UI
   │
2. Next.js → POST /api/v1/projects {repo_url, name}
   │
3. FastAPI validates URL, creates Project record (status: "analyzing")
   │
4. FastAPI creates Job record (status: "queued")
   │
5. FastAPI enqueues job in Redis (ARQ queue)
   │
6. Returns {project_id, job_id} to frontend
   │
7. Frontend starts polling GET /api/v1/jobs/{job_id} every 2 seconds
   │
8. ARQ Worker picks up job and runs pipeline:
   │
   ├── Stage 1 (0-15%): Clone repository (shallow, --depth 1)
   ├── Stage 2 (15-25%): Build file inventory (walk tree, detect languages)
   ├── Stage 3 (25-45%): Parse AST (tree-sitter per language)
   ├── Stage 4 (45-60%): Compute metrics + detect debt
   ├── Stage 5 (60-70%): Analyze dependencies (registry API lookups)
   ├── Stage 6 (70-90%): AI analysis (Claude/OpenAI for recommendations)
   └── Stage 7 (90-100%): Calculate modernization score
   │
9. Each stage updates job progress in Redis + PostgreSQL
   │
10. Frontend polling detects completion → redirects to results
   │
11. Dashboard renders analysis results from PostgreSQL
```

---

## Repository Analysis Pipeline

### Stage Details

#### Stage 1: Repository Cloning

```python
# Shallow clone for speed (no history needed for static analysis)
git clone --depth 1 --single-branch <repo_url> <temp_dir>
```

- Uses user's GitHub OAuth token for private repos
- 120-second timeout
- Max 500 MB repo size
- Temp directory with auto-cleanup

#### Stage 2: File Inventory

Walks the repository tree and builds a file inventory:

```python
SKIP_DIRS = {'.git', 'node_modules', '__pycache__', 'venv', '.venv',
             'dist', 'build', '.next', 'vendor', 'target'}

# For each file: path, extension, LOC, size, language
```

#### Stage 3: AST Parsing (tree-sitter)

Parses each source file using tree-sitter grammars:

| Extraction | Purpose |
|-----------|---------|
| Functions | Name, LOC, params, complexity, nesting |
| Classes | Name, methods, inheritance |
| Imports | Module, names, relative/absolute |

#### Stage 4: Metrics & Debt Detection

**Metrics computed:**
- Cyclomatic complexity (per function)
- Cognitive complexity (per function)
- Nesting depth (per function)
- LOC (per file, per function)
- Comment ratio (per file)
- Import count (per file, coupling indicator)

**Debt rules (12+ built-in):**
- High/critical complexity
- Long functions (>60 LOC)
- Deep nesting (>4 levels)
- Too many parameters (>5)
- God classes (>20 methods)
- Large files (>500 LOC)
- Missing documentation
- Security issues (regex-based)

#### Stage 5: Dependency Analysis

Parses package manifests and checks registries:

```
package.json    → npm registry API
requirements.txt → PyPI API
pom.xml         → Maven Central API
```

For each dependency:
- Current vs latest version
- Days behind latest
- Known CVEs (GitHub Advisory Database)
- Deprecation status
- License type

#### Stage 6: AI Analysis

**Two-tier approach:**
1. **Bulk analysis (cheap model)**: Per-file analysis for semantic issues
2. **Synthesis (powerful model)**: Cross-repo recommendations

#### Stage 7: Scoring

Weighted composite score across 7 dimensions → letter grade (A-F).

---

## AI Pipeline

### Model Routing Strategy

| Task | Model | Cost |
|------|-------|------|
| File-level analysis | Claude Haiku / GPT-4o-mini | ~$0.10/repo |
| Recommendation synthesis | Claude Sonnet / GPT-4o | ~$0.50/repo |
| On-demand refactoring | Claude Sonnet / GPT-4o | ~$0.10/request |

### Chunking Strategy

```
1. tree-sitter extracts functions/classes from source files
2. Small files (<32KB) → sent whole to LLM
3. Large files → split by AST boundaries (functions, classes)
4. Each chunk includes: file path, language, existing metrics
5. Responses parsed as structured JSON
```

### Cost Optimization

- 80% of analysis is deterministic (tree-sitter + rules) → free
- LLM used for semantic understanding only (20%)
- Results cached per commit SHA → no re-analysis of unchanged code
- Estimated cost: **$0.50–$5.00 per repository**

---

## Database Design

### Key Design Decisions

1. **UUID primary keys** — globally unique, no sequential leak
2. **JSONB columns** — flexible storage for variable-shape data
3. **Cascading deletes** — project deletion cleans up all related data
4. **pgvector extension** — future vector search capability
5. **Timestamps everywhere** — full audit trail

### Entity Relationships

```
User (1) ──→ (N) Project
Project (1) ──→ (N) Analysis
Project (1) ──→ (N) Job
Analysis (1) ──→ (N) FileMetric
Analysis (1) ──→ (N) DebtItem
Analysis (1) ──→ (N) DependencyFinding
Analysis (1) ──→ (N) Recommendation
Analysis (1) ──→ (1) ModernizationScore
```

---

## Authentication Flow

### GitHub OAuth Flow

```
1. User clicks "Sign in with GitHub"
2. Auth.js redirects to GitHub OAuth consent screen
3. User authorizes (grants 'repo' scope)
4. GitHub redirects back with authorization code
5. Auth.js exchanges code for access token
6. Auth.js creates JWT session
7. Frontend syncs user to backend (POST /auth/sync)
8. Backend upserts user record with encrypted GitHub token
9. User redirected to dashboard
```

### Token Security

- GitHub access tokens encrypted with Fernet (AES-128-CBC)
- JWT session tokens signed with AUTH_SECRET
- Tokens never exposed to client-side JavaScript
- Session cookies are httpOnly, secure, sameSite=lax

---

## Background Job System

### ARQ (Async Redis Queue)

```
Producer (FastAPI) ──→ Redis Queue ──→ Consumer (ARQ Worker)
                                        │
                                  Progress Updates
                                        │
                                   Redis + PostgreSQL
```

### Job Lifecycle

```
QUEUED → RUNNING → COMPLETED
                 → FAILED (with error message)
```

### Configuration

| Setting | Value | Rationale |
|---------|-------|-----------|
| Max concurrent jobs | 3 | Prevent resource exhaustion |
| Job timeout | 600s (10 min) | Large repos may take time |
| Max retries | 2 | Transient failures (network, API) |
| Health check interval | 30s | Detect dead workers |

---

## Security Architecture

### Defense in Depth

| Layer | Protection |
|-------|-----------|
| Network | HTTPS everywhere (Vercel/Railway enforce TLS) |
| Authentication | GitHub OAuth (no password storage) |
| Authorization | JWT tokens, route-level middleware |
| Input Validation | Pydantic schemas on all endpoints |
| SQL Injection | SQLAlchemy ORM (parameterized queries) |
| CORS | Strict origin whitelist |
| Rate Limiting | slowapi (100 req/min per user) |
| Secret Storage | Fernet encryption for tokens at rest |
| Repo Cloning | Temp dir, auto-cleanup, size limits |

### Security Checklist

- [x] No passwords stored (OAuth only)
- [x] Secrets in environment variables
- [x] GitHub tokens encrypted at rest
- [x] CORS whitelist configured
- [x] Input validation on all endpoints
- [x] Parameterized database queries
- [x] Rate limiting enabled
- [x] Temp files auto-cleaned
- [x] Repository size limits enforced

---

## Scalability Considerations

### Current MVP Limits

| Metric | Limit |
|--------|-------|
| Concurrent analyses | 3 |
| Max repo size | 500 MB |
| Max files per repo | 5,000 |
| Max file size | 1 MB |

### Future Scaling Path

1. **Horizontal worker scaling** — Add more ARQ workers
2. **Database read replicas** — Split read/write traffic
3. **Redis cluster** — Scale queue throughput
4. **S3 for repo storage** — Offload filesystem
5. **CDN for frontend** — Vercel edge network
6. **Connection pooling** — PgBouncer for database connections
7. **Caching layer** — Redis cache for analysis results
