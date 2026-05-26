# HyKr Build Challenge — Submission Tracker

> **Final deadline**: Sunday, 31 May 2026
> **Target submission**: Friday, 29 May 2026 (2-day buffer)
> **Today**: 26 May 2026 — **5 days remaining**

---

## Submission Requirements Checklist

- [ ] GitHub repo link (public, clear folder structure)
- [ ] 2-minute demo video (key user journey, problem → interaction → features)
- [ ] Concise technical documentation (architecture, stack, components, deployment)
- [ ] Working MVP link (stable, real user flows)
- [ ] Submission form filled out
- [ ] Test credentials / usage instructions included

---

## State of the Project — What We Have

### Strengths to Lean On in the Pitch

| Feature | Why judges care |
|---------|----------------|
| Real PR creation with AI-refactored code | Most competitors only suggest — we ship code |
| Webhook auto-cleanup on merge | Production-grade thinking, closes the loop |
| Prompt caching shipped | Shows AI cost-awareness |
| Multi-language tree-sitter (Py/JS/TS/Java) | Enterprise-relevant, not Python-only |
| Modernization score (A–F, 0–100) | Memorable, demoable, tweetable |
| 7-phase intelligence roadmap | Vision beyond MVP |
| Three-tier deployed architecture | Real product, not a notebook |

### One-line pitch

> CodeLens AI = modernization score + auto-fix PRs for legacy codebases.
> Detect technical debt. Ship the fix. Merge it. We clean up.

---

## Retrospective

### What Went Well ✅

- [x] Working end-to-end MVP (FE + API + worker + DB + queue)
- [x] Deployed live on Vercel + Railway
- [x] GitHub OAuth working
- [x] Real PR creation, not mockups
- [x] Multi-language AST parsing
- [x] Prompt caching implemented
- [x] Webhook for merge-detection wired
- [x] Documentation depth (CLAUDE.md, ARCHITECTURE.md, API.md, DEVELOPMENT.md, ROADMAP.md)

### What Did Not Go Well ⚠️

- [ ] No demo video yet — **biggest gap**
- [ ] Empty first-time UX (no sample repo, 3-min wait)
- [ ] Loader UI had bugs (fixed today, commit `917b029`)
- [ ] No "Dismiss" button on recommendations
- [ ] Re-analyze brings back fixed recs (expected, but confusing UX)
- [ ] No retry logic on AI failures
- [ ] No rate limiting → cost-blowout risk on demo day
- [ ] Cost story not visible in UI
- [ ] No test coverage badge
- [ ] Branding/positioning generic

---

## 5-Day Plan to Win 1st Prize

### Day 1 — 26 May (Tue) — Stability + Sample Data ✅

- [x] Add **"Try with sample repo"** buttons on New Project page
  - [x] 3 curated sample repos (normalize-url / pallets/flask / expressjs/express)
  - [x] One-click triggers analysis with no manual URL entry
- [x] Add **graceful AI retry** with exponential backoff in `ai_pipeline.py`
  - [x] 3 tries with 1s/2s/4s backoff + jitter
  - [x] Catches 408/429/500/502/503/504/529, timeouts, connection errors
  - [x] Applies to both Anthropic + OpenAI providers
- [x] Add per-user **rate limit** (10 analyses/day, configurable)
  - [x] Redis fixed-window counter (`ratelimit:{user}:analysis:{YYYYMMDD}`)
  - [x] `MAX_ANALYSES_PER_USER_PER_DAY` env var (default 10)
  - [x] 429 response with `Retry-After` header on exceed
  - [x] `GET /api/v1/projects/quota/analyses` endpoint for UI to peek

### Day 2 — 27 May (Wed) — UX Polish for Demo

- [x] **Dismiss button** on each recommendation card
  - [x] Backend: `DELETE /api/v1/recommendations/{id}`
  - [x] Frontend: trash icon + optimistic remove from list
- [x] **Estimated AI cost display** ("This analysis used $X.XX of AI compute")
  - [x] Track tokens via contextvar in ai_pipeline.py
  - [x] Show on overview tab (with token count)
- [x] **Empty-state CTAs** on debt/deps/AI tabs improved
- [ ] **Loading skeletons** consistent across all tabs
- [ ] **Polish error states** — friendly messages, not raw API errors

### Day 3 — 28 May (Thu) — Demo Video (2 min hard cap)

Structure:

```
0:00-0:15  Hook: "Every enterprise has legacy code rotting silently.
                 CodeLens AI scores it, fixes it, and ships PRs."

0:15-0:35  Sign in with GitHub → paste repo URL → analysis runs

0:35-0:55  Score gauge + sub-scores → drill into Tech Debt tab

0:55-1:25  AI Insights tab → click "Create Fix PR" → show actual
           GitHub PR with refactored code

1:25-1:45  Merge PR in GitHub → switch back → recommendation gone

1:45-2:00  "Built by [Nilu] in [N weeks].
            github.com/...  try it at legacy-modernization-platform.vercel.app"
```

Checklist:

- [ ] Pick demo repo (small, recognizable, with real issues — e.g., known Electron app)
- [ ] Pre-record analysis (or use sample-repo button) to avoid live 3-min wait
- [ ] Record with OBS or Loom (1080p, clear audio)
- [ ] Background music (instrumental, copyright-free)
- [ ] Add captions
- [ ] Hard cap 2:00 — re-record if over
- [ ] Upload to YouTube unlisted
- [ ] Test the link from a different browser/account

### Day 4 — 29 May (Fri) — Landing + README + Submit

#### Landing page

- [ ] Hero with animated score gauge
- [ ] 3 feature cards: Score / Detect / Fix
- [ ] One product screenshot
- [ ] CTA: "Sign in with GitHub"

#### Repo README

- [ ] Live MVP link at the top
- [ ] Demo video embed
- [ ] 1-minute "what is this" para
- [ ] Architecture diagram (link to ARCHITECTURE.md)
- [ ] "Run locally in 5 commands" section
- [ ] Tech stack badges (Next.js / FastAPI / Postgres / Anthropic)
- [ ] License + contributing note

#### Submission form

- [ ] Write all form answers in a draft doc first
- [ ] Test credentials note: "Sign in with any GitHub account — analyses are scoped per user."
- [ ] Polish problem statement (legacy modernization pain → market size → our wedge)
- [ ] Submit by **Friday afternoon**

### Day 5 — 30 May (Sat) — Buffer / QA

- [ ] Watch own demo video end-to-end
- [ ] Click every button on live MVP from a fresh browser session
- [ ] Have a friend try the MVP cold without explanation — fix anything they get stuck on
- [ ] Verify all links in submission form work
- [ ] Monitor Railway logs for any errors during testing
- [ ] If issues found → fix and re-submit

### Day 6 — 31 May (Sun) — Deadline

- [ ] Do nothing. Already submitted Friday.

---

## Risk Ranking — Watch These

| # | Risk | Mitigation |
|---|------|-----------|
| 1 | Demo video quality | Spend full Day 3 — script, record, edit, no shortcuts |
| 2 | First-time UX friction | Sample-repo button (Day 1) removes 3-min wait |
| 3 | Stability under load | Railway upgrade for one week, retry logic, rate limit |
| 4 | Generic positioning | Sharpen one-line pitch, lean on "ship PRs, not suggestions" |
| 5 | Cold start on Railway free tier | Upgrade or use keep-alive ping during judging window |

---

## Hidden Wins to Mention in Submission

When asked "what makes this different":

1. **Closes the loop** — detect → fix → PR → merge → cleanup (most stop at detect)
2. **Cost engineering** — prompt caching, two-tier AI strategy ($0.50–$5/repo not $50)
3. **Production thinking** — webhook signature verification, JWT auth, background jobs
4. **Multi-language** — not a Python-only toy
5. **Roadmap depth** — 7 phases planned, RAG + agents + verification next
6. **Real artifact** — judges can fork the codelens/fix-* branch and inspect the AI's actual code changes

---

## Win Condition

> Judges open the link → sample repo loads in <5s with pre-computed analysis →
> they click "Create Fix PR" → see a real GitHub PR with real refactored code →
> they think *"holy shit, this actually works."*

---

## Status Log

> **Convention**: Append a one-line entry under each day as it's completed. Move checkboxes to ✅ once done.

### 26 May 2026

- Loader UI fix shipped (`917b029`)
- AI disclaimer banner added (`1064775`)
- Roadmap doc added (`2cb9a98`)
- Submission tracker created (this file)

### 27 May 2026

- Day 1 shipped: AI retry, rate limit, sample repos
- Next: dismiss button + cost display + empty-state CTAs

### 28 May 2026

- Day 2 shipped: dismiss button (DELETE endpoint + trash icon + optimistic remove), AI cost display (contextvar token tracking → stored in analysis.summary), improved empty states on debt/deps tabs

### 28 May 2026

_(pending)_

### 29 May 2026

_(pending)_

### 30 May 2026

_(pending)_
