# AGENTS.md — Flagger

This file is the canonical context document for AI coding agents (Codex, Claude Code, etc.)
working in this repo. Read this before making changes. It supersedes assumptions from
training data about "typical" project structure — this project has specific, deliberate
conventions documented below.

---

## What Flagger Is

Flagger is an **audit-trail SaaS dashboard** for AI agent activity in GitHub repositories.
It gives tech leads and staff engineers a single, ordered, traceable view of everything AI
agents (Claude Code, Codex, Devin, Aider, etc.) have done in a codebase — queryable,
filterable, and linked to process context (CI status, review status, risk).

**Core value prop:** documentation and traceability, not code quality analysis.
Primary question Flagger answers: *"Everything AI touched in this repo — show it to me,
ordered, traceable, in one place."*
Secondary question (risk scoring, v2): *"Of everything that happened, what actually needs
my attention before it ships?"*

Flagger is explicitly **not** a code quality reviewer (that's CodeRabbit's territory).
It tracks provenance and process — who/what wrote code and how much oversight it got —
regardless of whether the code itself is well-written.

**Target users:**
- Primary: tech lead / staff engineer — cross-repo, cross-contributor view, budget authority
- Secondary: individual developer — same feed, scoped to their own agent activity

**Competitive position:** complementary to **git-ai** (open-source Git extension with
per-developer CLI, Git Notes-based attribution at `refs/notes/ai`). Flagger's differentiator
is **zero developer-side setup** — connect a GitHub repo via webhook once, get immediate
visibility. Flagger reads git-ai notes as an optional enhanced data source when present.

---

## Architecture

```
GitHub Webhooks → FastAPI backend → Supabase (PostgreSQL) → React dashboard
```

Monorepo layout:
```
flagger/
├── extension/        ← VS Code extension, DEFERRED (not active development)
├── backend/          ← FastAPI: webhook receiver, enrichment, attribution, scoring, REST API
└── dashboard/        ← React frontend (in progress)
```

Backend file structure:
```
backend/
├── main.py                        ← FastAPI app, webhook route, event router
├── database.py                    ← SQLAlchemy async engine + session factory
├── AttributionResolver.py         ← git-ai note fetch + heuristic fallback
├── scoring.py                     ← compute_risk() function
├── db/
│   └── repos.py                   ← get_repo(), get_pull_request_id() helpers
├── handlers/
│   ├── PullRequests.py            ← handle_pull_request()
│   ├── WorkflowRun.py             ← handle_workflow_run()
│   ├── PullRequestReview.py       ← handle_pull_request_review()
│   └── Push.py                    ← handle_push()
└── migrations/
    └── 001_v1_schema.sql          ← full DB schema
```

**Ownership split:** Aaron owns backend/attribution/API logic. Collaborator owns the
Supabase-hosted database/infrastructure side. **Any schema migration must be synced with
the collaborator's hosted schema before or immediately after applying DDL changes.**

---

## Hard Conventions — Do Not Deviate Without Explicit Discussion

1. **Raw SQL via `text()`, not an ORM model layer.** Schema was defined in SQL first
   (`migrations/001_v1_schema.sql`). SQLAlchemy async is used purely as a connection/session
   layer with bound-parameter raw queries. Do not introduce declarative ORM models unless
   explicitly asked.
2. **asyncpg + PgBouncer:** Supabase uses PgBouncer in transaction mode, which does not
   support prepared statements. The engine is created with
   `connect_args={"statement_cache_size": 0}`. Never remove this.
3. **Datetime handling:** asyncpg requires real `datetime` objects, not ISO strings. All
   incoming GitHub timestamp fields go through a local `parse_dt()` helper
   (`datetime.fromisoformat(value.replace("Z", "+00:00"))`). Every handler file currently
   defines its own copy of `parse_dt()` — if refactoring, consider consolidating to a shared
   utils module, but don't do this silently as a side effect of an unrelated change.
4. **Import path conflict:** `database.py` (file, engine/session) and `db/` (folder, query
   helpers) intentionally do not share a name — this was a bug fix. Do not rename `db/` to
   `database/`.
5. **Push payload quirk:** push webhook commit objects have `author.name`/`author.email`
   but no `author.login`. Always use `.get("login")`, never `["login"]`, when reading commit
   author identity from push payloads.
6. **Cursor-based pagination**, not offset, for timeline/feed endpoints.
7. **API owns data normalization, not presentation.** Don't push formatting/display logic
   (e.g. relative timestamps, risk color mapping) into backend responses — that's the
   dashboard's job.
8. **Idempotent upserts everywhere.** Every webhook handler upserts on GitHub's own stable
   ID (`github_pr_number`+`repo_id`, `github_run_id`, `github_review_id`, commit `sha`) since
   GitHub redelivers webhooks. New handlers must follow this pattern.
9. **Windows / Python 3.13 dev environment.** Be mindful of path separators and shell syntax
   in any suggested commands.

---

## Database Schema (six tables, `backend/migrations/001_v1_schema.sql`)

```
repos
  ↓
  ├── commits ──→ file_changes
  │     ↓ (nullable FK: pull_request_id)
  │     pull_requests
  │       ↓
  │       ├── ci_runs
  │       └── reviews
```

Key points:
- `commits.pull_request_id` is nullable and linked via `repo_id` + `head_branch` lookup
  against open PRs (added to fix a bug where it was always null — see below).
- `pull_requests.head_branch` was added via migration to support that linkage.
- Risk fields (`risk_no_review`, `risk_ci_unclean`, `risk_sensitive_path`,
  `risk_large_unreviewed`, `risk_direct_to_main`, `risk_level`) are computed at push time
  with defaults and are **not yet recomputed** when CI/review data arrives later — this is
  a known deferred improvement.
- **Supabase RLS is currently disabled** — flagged security concern. The correct fix is to
  enable RLS with **no policies (default-deny)** on all six tables. This closes public
  PostgREST exposure without affecting the backend's direct Postgres connection. This should
  be treated as a near-term priority, not nice-to-have.

---

## Attribution Architecture (Two-Mode)

1. **Enhanced mode:** if a commit has a git-ai Git Note at `refs/notes/ai`
   (`AttributionResolver.fetch_git_ai_note`), use it directly.
   `attribution_source = "git_ai_notes"`, `attribution_confidence = "certain"`.
2. **Standard/heuristic mode (fallback):** bot-account login matching (e.g.
   `claude-ai[bot]`, `devin-ai-integration[bot]`), co-author trailer parsing
   (`Co-authored-by: ...`), known-agent lookup tables.

Webhooks trigger the pipeline; **enrichment calls (diff fetch, git-ai note check) are
sequential follow-ups, not redundant duplicate work** — this distinction matters when
reasoning about call ordering/performance.

### Agent coverage — phased rollout
| Phase | Agents | Status |
|---|---|---|
| 1 (ship now) | Claude Code, Codex, Devin, Aider | Active — GitHub-visible, high confidence |
| 2 (next) | Lovable, Replit Agent, Base44 | Not started |
| 3 (later) | Cursor Agent mode, Copilot Agent | Not started, needs API work |
| 4 (deferred) | Cursor/Copilot inline suggestions, ChatGPT copy-paste | Requires VS Code extension — invisible at git layer |

Attribution confidence must always be shown explicitly in UI (e.g. "Devin (certain)" vs
"Heuristic match (suspected)") — never flatten confidence into a plain agent-name list.

---

## Risk Scoring (v1 — simple, v2 — deferred ML approach)

`backend/scoring.py::compute_risk()` — currently a simple additive flag-count model:
0 flags → low, 1 → medium, 2 → high, 3+ → critical. This is intentionally simple for v1.
**Do not over-engineer this function** unless explicitly asked to build v2.

v2 plan (deferred, not started): use Claude via the Batch API to generate labeled training
data, then fine-tune a smaller open-source model for risk classification. This is a future
initiative, not current scope — don't scaffold it preemptively.

---

## Current State (update this section as work progresses)

**Done:**
- All four webhook handlers (`handle_pull_request`, `handle_workflow_run`,
  `handle_pull_request_review`, `handle_push`) implemented, tested via `webhook_test.py`,
  verified against real Supabase writes.
- Three REST read endpoints implemented and returning correct responses:
  `GET /activity/recent`, `GET /repos/{owner}/{name}/timeline`,
  `GET /repos/{owner}/{name}/prs/{number}`.
- Fixed: commits always inserting with `pull_request_id = null` — added `head_branch` to
  `pull_requests`, updated `handle_pull_request` to capture it, updated `handle_push` to
  look up open PRs by `repo_id` + `head_branch`.
- React tech-lead activity view implemented with cursor pagination, repository/contributor/
  agent/risk/confidence filters, search, summary metrics, loading/error/empty states, and a
  commit evidence inspector. The inspector exposes attribution confidence, diff totals,
  review/risk signals, CI/review context, and the GitHub commit link.
- Per-agent breakdown implemented as a dedicated Agents view. It reports commit share,
  repository and contributor coverage, certain-vs-suspected attribution, review-needed
  counts, diff totals, and last activity. Selecting an agent returns to the activity ledger
  with that agent filter applied.
- Activity API support added for the dashboard: `GET /activity/summary`,
  `GET /activity/facets`, and `GET /activity/agents`. The agents endpoint uses a raw SQL
  aggregate and does not add an ORM layer or schema migration.
- Subtle state-driven motion added for the evidence inspector and expanded summary details,
  with `prefers-reduced-motion` support. Dashboard production build and ESLint both pass.

**Not done / on the horizon:**
- Live browser QA of the activity and Agents views against a running backend/Supabase data
  set. Automated build/lint checks pass, but the local servers could not be kept running in
  the agent environment used for the latest implementation session.
- Risk score badges as a first-class expandable UI. Review state and contributing signals
  are present, but the full risk-badge interaction remains to be built.
- Full PR/commit detail view, including files touched and richer CI/review context. The
  current evidence inspector is commit-focused and does not yet fetch the PR detail endpoint.
- Repo selector/navigation beyond the existing activity filter.
- Supabase RLS fix: enable RLS with no policies (default-deny) on all six tables and sync the
  change with the collaborator who owns the hosted schema.
- Handoff document update (v4 → v5).
- Risk score recomputation when CI/review data arrives after initial push-time scoring.
- WebSocket backend emission and live-feed client; do not build the client before the backend
  emits updates.
- v2 risk model (Claude Batch API → fine-tuned small model)
- Deployment/release data — closing the loop from "agent wrote it" to "shipped to prod".

**Known technical debt to flag if encountered, not silently fix:**
- `parse_dt()` duplicated across handler files instead of shared
- `main.py` still contains dead/unused local functions (`handlePush`, `handleWorkflowRun`,
  `handlePullRequestReview`) that were superseded by the `handlers/` module versions but
  never removed — safe to delete, but confirm before doing so since Codex may not have full
  session context on why they're still there.

---

## Frontend (React Dashboard) Design Priorities

**Build the tech lead view first** — it's the superset. The individual dev view is
identical, just with a contributor filter pre-applied. Don't build two separate views.

Tech lead view components, in priority order:
1. Activity feed — all AI agent activity across repo(s), newest first, cursor-paginated
2. Per-agent breakdown / filter (Claude Code, Codex, Devin, Aider, human)
3. Risk score badges — glanceable, expandable to show contributing flags
4. PR/commit detail view — files touched, CI status, review status, attribution
   source + confidence
5. Repo selector

Later phase: WebSocket client for live feed updates (backend has native FastAPI support
for this but it is not implemented yet — don't build frontend WebSocket handling before
the backend emits anything).


## Non-Goals (explicitly out of scope unless the plan changes)

- Not a code quality/review tool
- Not competing with git-ai — complementary, reads its data format optionally
- Not building inline-suggestion tracking (Phase 4 agents) without the VS Code extension,
  which is explicitly deferred
- Not building risk-scoring ML infra (v2) until v1 audit trail feed is validated with users
