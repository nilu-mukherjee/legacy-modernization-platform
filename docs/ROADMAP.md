# CodeLens AI — Intelligence Roadmap

> **Purpose of this document**: Living plan for evolving CodeLens AI from a static-analysis-plus-one-shot-LLM tool into an agentic, self-improving code modernization platform.
>
> **Audience**: Any AI agent (Claude Code, Cursor, etc.) or human engineer picking up the project. Read top-to-bottom to understand current state, then jump to the active phase.
>
> **Update rule**: When a phase ships, move it from "Planned" to "Shipped" with the merge commit SHA and date. Add lessons learned in the phase's *Notes* section.

---

## Table of Contents

1. [Current State (Phase 0)](#phase-0--current-state-shipped)
2. [Phase 1 — RAG Foundation](#phase-1--rag-foundation-pgvector-code-search)
3. [Phase 2 — Agentic File Analysis](#phase-2--agentic-file-analysis-tool-use)
4. [Phase 3 — Multi-Agent Specialist Synthesis](#phase-3--multi-agent-specialist-synthesis)
5. [Phase 4 — Incremental Re-Analysis](#phase-4--incremental-re-analysis-git-diff)
6. [Phase 5 — Verification Loop](#phase-5--verification-loop-self-critique)
7. [Phase 6 — Conversational Codebase Q&A](#phase-6--conversational-codebase-qa)
8. [Phase 7 — Self-Improvement via Feedback](#phase-7--self-improvement-via-feedback)
9. [Cross-Cutting Concerns](#cross-cutting-concerns)
10. [Cost & Performance Targets](#cost--performance-targets)
11. [Explicit Non-Goals](#explicit-non-goals)

---

## Phase 0 — Current State (Shipped)

### Architecture as of 2026-05-26

```
┌─────────────────────────────────────────────────────────────────┐
│  Frontend (Next.js 15, Vercel)                                  │
│  - Dashboard, project detail, AI insights tab                   │
│  - Create Fix PR button (per-file AI refactor + GitHub commit)  │
└──────────────────┬──────────────────────────────────────────────┘
                   │ JWT (backendToken)
┌──────────────────▼──────────────────────────────────────────────┐
│  Backend (FastAPI, Railway)                                     │
│  - REST API /api/v1/*                                           │
│  - Webhook POST /api/v1/webhooks/github (PR-merge cleanup)      │
└──────────────────┬──────────────────────────────────────────────┘
                   │
       ┌───────────┴───────────┐
       ▼                       ▼
┌──────────────┐       ┌──────────────────┐
│ PostgreSQL   │       │ Redis            │
│ + pgvector   │◀──────│ ARQ queue        │
│ (unused yet) │       │ worker process   │
└──────────────┘       └──────────────────┘
                              │
                              ▼
                  ┌──────────────────────────┐
                  │ Analysis pipeline:       │
                  │ 1. git clone --depth 1   │
                  │ 2. inventory             │
                  │ 3. tree-sitter AST       │
                  │ 4. rule-based metrics    │
                  │ 5. dependency lookup     │
                  │ 6. AI synthesis (one-shot│
                  │ 7. scoring               │
                  └──────────────────────────┘
```

### What works

| Capability | Implementation | File |
|-----------|---------------|------|
| Static analysis | tree-sitter for Py/JS/TS/Java | `backend/app/services/ast_parser.py` |
| Debt detection | Rule-based (regex + AST) | `backend/app/services/debt_detector.py` |
| AI synthesis | One Anthropic call per analysis | `backend/app/services/ai_pipeline.py` |
| Prompt caching | `cache_control: ephemeral` on system blocks | `backend/app/services/ai_pipeline.py:155` |
| Recommendations | Stored with `affected_files` JSONB | `backend/app/models/recommendation.py` |
| Create Fix PR | Frontend GitHub API + per-file AI refactor | `frontend/src/components/analysis/create-pr-button.tsx` |
| Auto-delete on merge | GitHub webhook → delete recommendation | `backend/app/api/v1/routes/webhooks.py` |

### Known limitations (drives Phase 1+)

1. Files truncated to 16K chars before AI sees them — loses context for large files.
2. AI analyzes each file in isolation — no cross-file understanding.
3. Re-analyze runs full pipeline every time — no incremental mode.
4. No memory between analyses — system doesn't learn.
5. No verification that refactored code actually works.
6. pgvector extension installed but unused.

---

## Phase 1 — RAG Foundation (pgvector code search)

**Goal**: Index every analyzed repo into pgvector. Retrieve semantically similar code chunks at refactor/analysis time so the LLM sees relevant repo context, not just one truncated file.

**Status**: 🔲 Planned

### New tables

```sql
CREATE TABLE code_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    analysis_id UUID NOT NULL REFERENCES analyses(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    start_line INT NOT NULL,
    end_line INT NOT NULL,
    kind TEXT NOT NULL,  -- function | class | module | block
    name TEXT,           -- function/class name if applicable
    content TEXT NOT NULL,
    embedding vector(1024) NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX code_chunks_analysis_idx ON code_chunks(analysis_id);
CREATE INDEX code_chunks_embedding_idx ON code_chunks
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);
```

### New files

| File | Responsibility |
|------|---------------|
| `backend/alembic/versions/0002_code_chunks.py` | Migration |
| `backend/app/models/code_chunk.py` | SQLAlchemy model |
| `backend/app/services/embeddings.py` | Provider abstraction (Voyage / OpenAI fallback) |
| `backend/app/services/code_indexer.py` | Chunking + embedding + persistence |
| `backend/app/services/retriever.py` | `retrieve_similar(query, project_id, k)` |

### Worker integration

After Stage 3 (AST parse) in `analysis_worker.py`, add Stage 3.5:

```python
await _update_progress(db, jid, 50, "Indexing code chunks")
await index_repo_chunks(repo_path, analysis.id, ast_results, db)
```

### Refactor flow integration

`generate_refactoring()` in `ai_pipeline.py` retrieves top-5 similar chunks from the same project before building the prompt:

```python
context_chunks = await retriever.retrieve_similar(
    query=code,
    project_id=project_id,
    k=5,
    exclude_path=file_path,
)
system = REFACTOR_SYSTEM + "\n\nExisting patterns in this repository:\n" + format_chunks(context_chunks)
```

### Embedding provider order

1. `VOYAGE_API_KEY` set → `voyage-code-3` (1024 dims)
2. Else `OPENAI_API_KEY` set → `text-embedding-3-small` (1536 dims; truncate to 1024 or use separate column)
3. Else log warning + skip indexing (degrade to current behavior)

### Acceptance criteria

- [ ] Re-analyzing a 1K-LOC repo produces ≥50 chunks in `code_chunks`
- [ ] `POST /refactor` with `file_content` includes top-5 retrieval context in the prompt
- [ ] Cosine search `<10ms` for projects with <10K chunks
- [ ] Embedding cost <$0.05 per repo analysis

---

## Phase 2 — Agentic File Analysis (tool use)

**Goal**: Replace blind file truncation with a Claude agent that uses tools to navigate the repo intelligently — reads what it needs, follows imports, checks how functions are used elsewhere.

**Status**: 🔲 Planned (depends on Phase 1 for `retrieve_similar` tool)

### New module: `backend/app/services/analyst_agent.py`

```python
TOOLS = [
    {"name": "read_file",         "input_schema": {...}},  # full file content
    {"name": "read_lines",        "input_schema": {...}},  # specific line range
    {"name": "search_code",       "input_schema": {...}},  # ripgrep wrapper
    {"name": "get_imports",       "input_schema": {...}},  # from AST parse results
    {"name": "get_callers",       "input_schema": {...}},  # who calls this function
    {"name": "retrieve_similar",  "input_schema": {...}},  # pgvector query
    {"name": "get_file_metrics",  "input_schema": {...}},  # complexity/LOC for any file
]

async def analyst_loop(
    repo_path: Path,
    target_file: str,
    analysis_id: UUID,
    db: AsyncSession,
    max_iterations: int = 15,
) -> dict:
    """Agent runs until end_turn or max iterations. Returns structured analysis."""
```

### System prompt (cached)

```
You are a senior code reviewer with full repo access. Use the tools to:
1. Read the target file
2. Follow imports to understand context
3. Check how affected functions are used elsewhere
4. Retrieve semantically similar code to compare patterns
5. Only then produce your analysis

Be thorough but stop when you have enough context. Avoid tool calls that don't change your conclusion.
```

### Tool execution

| Tool | Implementation |
|------|---------------|
| `read_file` | Direct filesystem read from cloned repo path |
| `read_lines` | Same, with `linecache` slicing |
| `search_code` | `subprocess.run(["rg", "--json", pattern, repo_path])` |
| `get_imports` | Query AST results table (no LLM round-trip) |
| `get_callers` | Symbol cross-reference table (new, populated in Stage 3) |
| `retrieve_similar` | pgvector query from Phase 1 |
| `get_file_metrics` | Query `file_metrics` table |

### Integration

Worker stage 4 (currently calls `analyze_file_with_ai` per file) replaced with:
- For files with `complexity > 10` OR `loc > 200`: run agent loop
- Else: keep current cheap one-shot Haiku call

This keeps cost bounded — only spend agent tokens on files that warrant deep analysis.

### Acceptance criteria

- [ ] Agent invokes 3-10 tools on average per complex file
- [ ] Analysis quality (human spot-check) improves on files >500 LOC
- [ ] Total cost per repo ≤ 1.5× current cost
- [ ] No infinite tool loops (max 15 iterations hard cap)

---

## Phase 3 — Multi-Agent Specialist Synthesis

**Goal**: Replace single `generate_recommendations()` synthesis call with N parallel specialist agents, each focused on one dimension.

**Status**: 🔲 Planned

### Directory structure

```
backend/app/services/agents/
├── __init__.py
├── base.py              # SpecialistAgent ABC + shared utilities
├── security_agent.py    # OWASP Top 10, secrets, injection, auth bypass
├── performance_agent.py # N+1 queries, blocking I/O, bundle size, hot loops
├── architecture_agent.py # coupling, god classes, circular deps, layering
├── testing_agent.py     # missing tests, untested branches, mock abuse
├── upgrade_agent.py     # outdated deps, deprecated APIs, EOL languages
└── synthesizer.py       # dedupe + prioritize + format
```

### `SpecialistAgent` ABC

```python
class SpecialistAgent(ABC):
    category: str           # security | performance | architecture | testing | upgrade
    model: str              # default Haiku, override per agent
    system_prompt: str      # cached, focused on this domain

    @abstractmethod
    async def analyze(
        self,
        analysis_id: UUID,
        metrics: dict,
        db: AsyncSession,
    ) -> list[RecommendationDraft]:
        ...
```

### Worker stage 6 replacement

```python
await _update_progress(db, jid, 75, "Running specialist agents")

specialists = [
    SecurityAgent(), PerformanceAgent(), ArchitectureAgent(),
    TestingAgent(), UpgradeAgent(),
]

drafts: list[list[RecommendationDraft]] = await asyncio.gather(
    *(s.analyze(analysis.id, scoring_metrics, db) for s in specialists),
    return_exceptions=True,
)

# Stage 6b: synthesizer dedupes + prioritizes
final_recs = await Synthesizer().merge(drafts, top_n=10)
```

### Why this works

- Each specialist's system prompt is short and focused → better signal
- Specialists run on Haiku in parallel → cheaper than one Sonnet call
- Specialist prompts cache independently → high cache hit rate across re-analyses
- Easy to add new specialists (e.g., `AccessibilityAgent` for frontend repos)

### Acceptance criteria

- [ ] 5 specialist agents implemented
- [ ] Synthesizer dedupes overlapping recs (e.g., security + architecture both flagging same file)
- [ ] Total wall-clock time ≤ current synthesis time (parallelism wins)
- [ ] Specialist outputs traceable in DB (`recommendation.source_agent` column)

---

## Phase 4 — Incremental Re-Analysis (git diff)

**Goal**: Re-analyze only changed files since last analysis. Massive cost + latency win on the typical "analyze → fix → re-analyze" loop.

**Status**: 🔲 Planned

### Schema changes

```sql
ALTER TABLE analyses ADD COLUMN commit_sha TEXT;
ALTER TABLE analyses ADD COLUMN base_analysis_id UUID REFERENCES analyses(id);
ALTER TABLE analyses ADD COLUMN is_incremental BOOLEAN DEFAULT FALSE;
```

### Worker logic

```python
async def run_analysis(ctx, job_id):
    last = await get_last_completed_analysis(project_id, db)
    current_sha = await git_rev_parse(repo_path, "HEAD")

    if last and last.commit_sha and last.commit_sha != current_sha:
        changed_files = await git_diff_files(repo_path, last.commit_sha, current_sha)
        if not changed_files:
            return await reuse_analysis(last, current_sha)
        return await incremental_analyze(last, changed_files, current_sha)

    return await full_analyze(repo_path, current_sha)
```

### Incremental steps

1. Run Stages 1-5 only on `changed_files`
2. Copy unchanged file metrics + chunks from `base_analysis_id`
3. Invalidate stale code chunks for changed files
4. Re-embed only changed chunks
5. Re-run specialists with updated metrics (Phase 3 integration)

### Acceptance criteria

- [ ] Re-analyze with 0 file changes completes in <5 sec
- [ ] Re-analyze with <10% files changed completes in <30 sec
- [ ] Full analysis path still works (cold start case)
- [ ] No stale data in `file_metrics`, `code_chunks`, `debt_items` after incremental run

---

## Phase 5 — Verification Loop (self-critique)

**Goal**: Don't trust the AI's refactored code blindly. Verify syntactically, structurally, and (when possible) by running tests.

**Status**: 🔲 Planned

### Pipeline

```
generate_refactoring(...)
       │
       ▼
syntax_check (tree-sitter parse)
       │
       ▼
ast_structure_check (preserve public signatures)
       │
       ▼
sandbox_test_run (if tests exist) ──────► run tests in isolated container
       │                                          │
       ▼                                          ▼
all checks pass                            critique + retry
```

### `backend/app/services/refactor_verifier.py`

```python
async def verify(
    original: str,
    refactored: str,
    language: str,
    file_path: str,
    test_files: list[Path] | None = None,
) -> VerificationResult:
    issues: list[str] = []

    if not parses_cleanly(refactored, language):
        issues.append("Syntax error in refactored code")

    if not preserves_signatures(original, refactored, language):
        issues.append("Public API signatures changed")

    if test_files and await has_sandbox_runner():
        result = await run_tests_in_sandbox(refactored, test_files, language)
        if not result.passed:
            issues.append(f"Tests failed: {result.summary}")

    return VerificationResult(ok=not issues, issues=issues)
```

### Retry loop

```python
async def generate_verified_refactoring(code, rec, language, file_path, max_retries=3):
    for attempt in range(max_retries):
        refactored = await generate_refactoring(code, rec, language, file_path)
        result = await verify(code, refactored, language, file_path)
        if result.ok:
            return refactored
        critique = "\n".join(result.issues)
        rec_with_critique = rec._replace(rationale=f"{rec.rationale}\n\nPrevious attempt failed:\n{critique}")
        rec = rec_with_critique
    raise RefactorVerificationError(result.issues)
```

### Sandbox options (pick one)

| Option | Pros | Cons |
|--------|------|------|
| Anthropic Code Execution Tool | Native, no infra | Python-only, beta |
| Docker container per request | Multi-language, isolated | Slow startup (~2s) |
| Modal/E2B sandbox service | Fast, multi-language | External dependency |

### Acceptance criteria

- [ ] Syntax + signature check runs on every refactor (always)
- [ ] Sandbox runs when test files detected (optional, gated by env var)
- [ ] Failed verifications retry up to 3× before surfacing to user
- [ ] PR flow includes verification result badge in PR description

---

## Phase 6 — Conversational Codebase Q&A

**Goal**: Chat sidebar on project page. User asks free-form questions about their code; agent uses Phase 2 tools + Phase 1 retrieval to answer.

**Status**: 🔲 Planned

### New tables

```sql
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    project_id UUID REFERENCES projects(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    title TEXT
);

CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role TEXT NOT NULL,  -- user | assistant | tool
    content JSONB NOT NULL,  -- text or tool_use/tool_result blocks
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### New endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /projects/{id}/chat/sessions` | List user's chat sessions |
| `POST /projects/{id}/chat/sessions` | Create new session |
| `GET /chat/sessions/{id}/messages` | Load history |
| `POST /chat/sessions/{id}/messages` | Send message → streamed response (SSE) |

### Streaming response

Use Anthropic SDK's streaming API. Frontend renders tokens as they arrive. Tool calls render as collapsible "Used tool: read_file(auth.py)" blocks.

### Acceptance criteria

- [ ] User can ask "Which file is the most complex?" and get a tool-grounded answer
- [ ] User can ask "Show me how authentication works" → agent reads files, summarizes
- [ ] Token streaming works end-to-end (<200ms first token)
- [ ] Session history persists across page reloads

---

## Phase 7 — Self-Improvement via Feedback

**Goal**: System learns from which recommendations users accept, modify, or dismiss. Future recommendations get few-shot examples from past accepted ones.

**Status**: 🔲 Planned

### Schema changes

```sql
ALTER TABLE recommendations ADD COLUMN outcome TEXT;
-- pending | accepted | dismissed | modified | merged | reverted
ALTER TABLE recommendations ADD COLUMN outcome_evidence JSONB DEFAULT '{}'::jsonb;
-- { "pr_url": ..., "merged_at": ..., "files_changed": [...], "user_edits": "..." }
ALTER TABLE recommendations ADD COLUMN outcome_at TIMESTAMPTZ;
```

### Outcome detection

| Event | Sets outcome to |
|-------|----------------|
| Webhook: PR merged on `codelens/fix-*` | `merged` |
| Webhook: PR closed without merge | `dismissed` |
| User clicks "Dismiss" button | `dismissed` |
| Webhook: PR force-pushed (user edited) | `modified` |
| Re-analysis no longer detects same issue | `accepted` (auto-inferred) |

### Feedback loop

At synthesis time (Phase 3 specialists), each agent retrieves:

```python
similar_accepted = await db.execute(
    select(Recommendation)
    .where(
        Recommendation.outcome.in_(["merged", "accepted"]),
        Recommendation.category == self.category,
        Recommendation.user_id == current_user.id,
    )
    .order_by(Recommendation.outcome_at.desc())
    .limit(3)
)
```

Inject as few-shot examples in the specialist's system prompt:

```
Examples of previously accepted recommendations in this user's projects:
[1] Title: "Replace hardcoded API key with env var"
    Files: [auth.py]
    User outcome: merged 3 days ago
[2] ...

Now generate recommendations for the current project.
```

### Acceptance criteria

- [ ] Webhook updates `outcome` correctly for merge/close/edit events
- [ ] Re-analysis flow auto-marks resolved recs as `accepted`
- [ ] Specialist agents include ≥1 few-shot example when 3+ accepted recs exist
- [ ] User can manually dismiss recs via UI button → API endpoint

---

## Cross-Cutting Concerns

### Observability

Add structured logging + metrics on every LLM call:

```python
logger.info("llm_call", extra={
    "agent": agent_name,
    "model": model,
    "input_tokens": resp.usage.input_tokens,
    "output_tokens": resp.usage.output_tokens,
    "cache_creation_input_tokens": resp.usage.cache_creation_input_tokens,
    "cache_read_input_tokens": resp.usage.cache_read_input_tokens,
    "latency_ms": elapsed,
    "project_id": project_id,
})
```

Tools to consider: Sentry (errors), Posthog or Logfire (events), Grafana for cost dashboards.

### Rate limiting

Per-user budget cap:

```
ANALYSIS_BUDGET_PER_USER_PER_DAY_USD = 5.00
```

Track via Redis counter. Reject new analyses when exceeded.

### Security

- Never include raw GitHub tokens in LLM prompts (always strip before sending)
- Verify webhook signatures (`GITHUB_WEBHOOK_SECRET`)
- Sandbox refactor verification — never `exec()` AI-generated code in-process
- Validate all tool-use inputs from the agent (whitelist file paths to repo root)

### Multi-tenancy

When opening to multiple orgs:
- Row-level security on all project-scoped tables
- Per-org embedding namespaces in pgvector (already implicit via `analysis_id`)
- Separate ARQ queues per org (high-priority for paid plans)

---

## Cost & Performance Targets

For a typical 5K-LOC repo:

| Scenario | Current | After Phase 1 | After Phase 4 | After Phase 7 |
|----------|---------|---------------|---------------|---------------|
| First analysis cost | $0.80 | $1.20 | $1.20 | $1.30 |
| First analysis time | 2-3 min | 2-3 min | 2-3 min | 2-3 min |
| Re-analyze (no changes) | $0.80 | $0.80 | **$0.01** | $0.01 |
| Re-analyze (10% changes) | $0.80 | $0.80 | **$0.12** | $0.12 |
| Refactor quality (1-10) | 5 | 7 (RAG) | 7 | 9 (few-shot) |

---

## Explicit Non-Goals

These are intentionally **not** on the roadmap:

- **Fine-tuning custom models** — RAG + good prompts beats this for code tasks
- **Custom embedding models** — Voyage / OpenAI are SOTA, no value in rolling our own
- **LangChain / LlamaIndex** — adds dependency weight; Anthropic SDK + asyncio handles agent loops cleanly
- **Switching off pgvector to Pinecone/Weaviate** — Postgres is sufficient until 10M+ chunks
- **Building our own LLM evals harness** — use Anthropic Workbench + offline notebooks
- **Real-time collaborative editing** — out of scope; this is an analysis tool, not an IDE
- **Self-hosted LLM (Ollama/vLLM)** — model quality matters more than cost at current scale

---

## How to Pick the Next Phase

Decision matrix (lower row = pick that phase next):

```
If users complain about refactor quality       → Phase 1 (RAG)
If users complain about cost on re-analyze     → Phase 4 (Incremental)
If users complain about generic recs           → Phase 3 (Multi-agent)
If users complain about AI hallucinating fixes → Phase 5 (Verification)
If users ask "how do I do X in my codebase"    → Phase 6 (Chat)
If users say "the AI keeps suggesting the same thing"  → Phase 7 (Feedback)
If a single file is too big to analyze well    → Phase 2 (Agentic)
```

Default order (each builds on previous): **1 → 4 → 3 → 2 → 5 → 7 → 6**

---

## Phase Status Tracker

| Phase | Status | Started | Shipped | Commit |
|-------|--------|---------|---------|--------|
| 0 — Baseline | ✅ Shipped | — | 2026-05-26 | `917b029` |
| 1 — RAG Foundation | 🔲 Planned | — | — | — |
| 2 — Agentic Analysis | 🔲 Planned | — | — | — |
| 3 — Multi-Agent | 🔲 Planned | — | — | — |
| 4 — Incremental | 🔲 Planned | — | — | — |
| 5 — Verification | 🔲 Planned | — | — | — |
| 6 — Conversational | 🔲 Planned | — | — | — |
| 7 — Feedback Loop | 🔲 Planned | — | — | — |

> **AI agents**: when starting work on a phase, mark its status as `🚧 In Progress`. When merged, mark `✅ Shipped` and fill in the commit SHA. Add a *Notes* subsection under that phase describing what changed vs. the plan and any lessons learned.
