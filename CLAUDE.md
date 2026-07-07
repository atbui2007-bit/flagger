# CLAUDE.md — Flagger

This is the canonical context file for Claude Code in this repo. Read it before making
changes. It describes what Flagger is, why it's built the way it is, and what "done"
looks like for launch. It does not contain a task list — task tracking lives in Notion.
Treat the conventions below as deliberate, not default scaffolding to "clean up."

---

## 1. What Flagger Is

Flagger is an **audit-trail SaaS product** for engineering teams adopting AI coding
agents. It answers one question for a tech lead: *"Everything AI touched in this repo —
show it to me, ordered, traceable, in one place."* A secondary, not-yet-validated
question is which of that activity actually needs attention before it ships (risk
scoring, intentionally v2).

Flagger is **not** a code quality reviewer — that's CodeRabbit's job. It tracks
provenance and process (who/what wrote code, how much oversight it got), not whether the
code is good.

**Differentiator:** zero developer-side setup. Competing tools like `git-ai` require a
CLI wrapper per developer. Flagger connects via a GitHub App webhook once, at the repo
level, and gets visibility immediately. Flagger treats `git-ai` as complementary, not a
competitor: if a repo already has `git-ai` Git Notes at `refs/notes/ai`, Flagger reads
them as a higher-confidence attribution source. Where `git-ai` isn't present, Flagger
falls back to its own heuristics.

**Primary users:** tech leads / staff engineers wanting a cross-repo, cross-contributor
view of AI-authored activity, with budget authority.
**Secondary users:** individual developers reviewing their own agent activity — the same
feed, scoped with a contributor filter. There is one view, not two products.

**Brand/product feel** (see `DESIGN.md` for full tokens): a quiet, dense, forensic
ledger — Linear's information density, Vercel's restraint, GitHub's familiarity with
SHAs/branches/diffs. Explicitly not a Datadog/Splunk-style observability wall, no
gamification, no color-only risk signals, no feed reflow on live updates.

---

## 2. What "Launched" Means

Flagger is launched when an external user can:

1. Click "Connect GitHub," install the Flagger GitHub App on one or more repos, and see
   activity start flowing in — with no CLI, no config file, no manual webhook setup.
2. Sign in, and only see data for repos/orgs they're authorized for (not everyone's data).
3. Open the dashboard and see a real, correctly-scoped activity feed: commits, PR/CI/
   review context, and an honestly-labeled attribution confidence per commit.
4. Trust that "low risk" is an achievable, meaningful state — not a badge that can
   mathematically never appear.
5. Use the product against a backend that isn't pointed at `localhost` and isn't relying
   on a single long-lived personal access token for GitHub API calls.

Everything below describes the system that supports that. Where the current
implementation doesn't yet match the target, that's called out explicitly so it isn't
mistaken for working behavior.

---

## 3. Architecture Overview

```
GitHub (webhooks + REST API)
        │
        ▼
FastAPI backend (webhook receiver → attribution → risk scoring → Postgres)
        │
        ▼
Supabase / PostgreSQL (raw SQL via SQLAlchemy async, RLS default-deny)
        │
        ▼
React dashboard (activity ledger, agent breakdown, evidence inspector)
```

Monorepo layout:
```
flagger/
├── backend/          FastAPI: webhooks, attribution, scoring, REST API
├── dashboard/        React (Vite + Tailwind + TanStack Query) tech-lead/dev activity view
└── extension/        VS Code extension — deferred, not active development
```

### Backend file structure
```
backend/
├── main.py                    FastAPI app, webhook signature verification, event router
├── database.py                async engine + session factory (asyncpg, PgBouncer-safe)
├── AttributionResolver.py     git-ai note fetch (enhanced) + heuristic fallback
├── scoring.py                 compute_risk() — flag-count model
├── db/
│   └── repos.py                get_repo(), get_pull_request_id() lookups
├── handlers/
│   ├── PullRequests.py         handle_pull_request()
│   ├── WorkflowRun.py          handle_workflow_run()
│   ├── PullRequestReview.py    handle_pull_request_review()
│   └── push.py                 handle_push() — commit ingestion, attribution, scoring
├── routers/
│   ├── activity.py             GET /activity/recent, /summary, /facets, /agents
│   ├── timeline.py             GET /repos/{owner}/{name}/timeline
│   └── prs.py                  GET /repos/{owner}/{name}/prs/{number}
└── migrations/
    └── 001_v1_schema.sql       full DB schema
```

---

## 4. Database

Six tables, defined in raw SQL (`backend/migrations/001_v1_schema.sql`), not an ORM
model layer:

```
repos
  └── commits ──→ file_changes
        └── (nullable FK) pull_requests
              ├── ci_runs
              └── reviews
```

- `commits.pull_request_id` is nullable and resolved at push time by looking up an open
  PR on `repo_id` + `head_branch` — pushes and PR-opened events arrive as separate
  webhooks, so this linkage is inferred, not given directly by GitHub.
- Risk fields on `commits` (`risk_level`, `risk_no_review`, `risk_ci_unclean`,
  `risk_sensitive_path`, `risk_large_unreviewed`, `risk_direct_to_main`) are computed
  once, at push time, from data available at that instant. They are **not** currently
  recomputed when later CI or review events arrive — a commit that gets reviewed after
  the fact does not have its risk score updated.
- RLS is enabled with default-deny (no policies) across all six tables. This closes
  public PostgREST exposure. It does not affect the backend, which connects as a
  `BYPASSRLS` role through the pooler.
- Soft-delete convention: any table representing installable/removable state (e.g. a
  future `installations` table for the GitHub App) uses `removed_at` with
  `WHERE removed_at IS NULL` on default reads. Hard deletes are not used — the audit
  trail must survive removal events.

**Conventions that are deliberate, not accidental:**
- Raw SQL via `text()` with bound params, not declarative ORM models. The schema was
  designed in SQL first.
- `SQLAlchemy` `Row` objects must be converted with `dict(row._mapping)` before FastAPI
  can serialize them — this has bitten every new endpoint so far; do it proactively.
- Cursor-based pagination (`(pushed_at, id)` tuple comparison), never offset — offset
  breaks under concurrent inserts and doesn't set up cleanly for a future WebSocket feed.
- Idempotent upserts on GitHub's own stable IDs (`github_pr_number`+`repo_id`,
  `github_run_id`, `github_review_id`, commit `sha`), because GitHub redelivers
  webhooks. Any new handler must follow this pattern.
- PgBouncer runs in transaction mode, which doesn't support prepared statements — the
  engine is created with `connect_args={"statement_cache_size": 0}`. Never remove this.
- Per-handler queries instead of mega-joins for multi-table reads (e.g. PR detail) —
  joining `pull_requests` + `commits` + `ci_runs` + `reviews` in one query would multiply
  rows whenever a PR has more than one commit or review.
- Database schema and infrastructure are owned jointly with a collaborator who is not on
  this Claude workspace. Any migration or schema change should be treated as a decision
  to be communicated, not just applied — the handoff doc is the sync mechanism.

---

## 5. Attribution (how Flagger knows *who* wrote a commit)

Two-mode resolver, `AttributionResolver.py`:

1. **Enhanced mode** — if the repo has `git-ai` Git Notes at `refs/notes/ai` for a
   commit, use that directly. `attribution_source = "git_ai_notes"`,
   `attribution_confidence = "certain"`. This is the preferred path when available.
2. **Heuristic fallback** — bot-account login matching (`claude-ai[bot]`,
   `devin-ai-integration[bot]`, etc.), `Co-authored-by:` trailer parsing against known
   agent names, otherwise `agent_type = "unknown"` with `attribution_confidence =
   "suspected"`.

Attribution confidence must always be surfaced explicitly in the UI — never flattened
into a plain agent-name list. "Devin (certain)" and "Heuristic match (suspected)" are
different claims and the product's credibility depends on not blurring that line.

**Agent coverage is phased.** Phase 1 (ship now): Claude Code, Codex, Devin, Aider —
these are GitHub-visible with high-confidence signals. Phase 2+ (Lovable, Replit Agent,
Cursor Agent mode, Copilot Agent) and Phase 4 (inline suggestions, invisible at the Git
layer — would require the VS Code extension) are explicitly out of scope until Phase 1
is validated with real usage.

**Known-broken component:** `fetch_git_ai_note()` currently calls
`GET /repos/{full_name}/git/notes/{sha}` — this is not a real GitHub REST endpoint. Git
notes are not exposed this way; retrieving them requires walking the `refs/notes/ai` ref
via the Git Data API (tree/blob lookups), not a direct per-commit note fetch. Enhanced
mode should be assumed non-functional until this is replaced. Do not build features on
the assumption that git-ai notes are currently being read successfully.

---

## 6. Risk Scoring (intentionally simple, v1)

`backend/scoring.py::compute_risk()` is an additive flag-count model: 0 flags → low,
1 → medium, 2 → high, 3+ → critical. This is deliberate — there is no real usage data
yet to train or validate anything more sophisticated, and building v2 (Claude Batch API
→ fine-tuned classifier) before v1 has real signal would be premature. Do not scaffold
v2 unless explicitly asked.

**Known structural issue:** in `handlers/push.py`, `risk_no_review` is currently
hardcoded to `True` for every commit at ingestion time (there is no review-status check
being performed yet — reviews arrive later, asynchronously, via a separate webhook).
Since `compute_risk()` returns `"low"` only when the flag count is exactly zero, and
`risk_no_review` is always `True` at the moment scoring runs, `"low"` cannot currently
be produced by the real pipeline. This is a floor problem in the calling code, not in
`compute_risk()` itself — the function is correct given its inputs. Any fix belongs in
how/when `risk_no_review` is set, not in the scoring math.

---

## 7. GitHub Integration

**Target state:** Flagger is a GitHub App (not a personal-access-token integration).
Installation happens per org/repo through GitHub's install flow, tokens are scoped to
the installation and refreshed automatically, and multiple installations across
different orgs/accounts are tracked and can be soft-removed without losing history.

**Current gap:** `push.py` and `AttributionResolver.py` both read a single static
`GITHUB_TOKEN` from the environment via `httpx` calls. This does not scale past one
GitHub account/org, has no per-installation scoping, and is the piece actively being
replaced by a GitHub App–based token flow (installation table, locked per-installation
token cache, a shared guard that checks repo + installation state before any webhook
handler proceeds). Until that migration is complete, treat any code path using
`os.getenv("GITHUB_TOKEN")` as temporary scaffolding, not the intended design — new
GitHub API calls should be written against the installation-scoped pattern, not copy
the static-token pattern forward.

Webhook signature verification (`X-Hub-Signature-256` HMAC check in `main.py`) is
already correct and should remain the first thing that happens on every webhook POST,
before any payload parsing.

---

## 8. Auth & Hosting (not yet implemented)

There is currently no authentication layer — the dashboard talks to a hardcoded
`http://localhost:8000` API base, and there is no concept of a logged-in user or
account boundary. For launch, the dashboard needs to only ever show data the
authenticated user/org is entitled to see; this is a hard requirement, not a nice-to-
have, since the product's core promise is a trustworthy audit trail. No production
hosting decision has been made yet for the backend.

---

## 9. Backend API (current)

- `POST /webhook` — single endpoint, GitHub event type read from `X-GitHub-Event`
  header, signature-verified, dispatched to the matching handler in `handlers/`.
- `GET /activity/recent` — cursor-paginated commit feed, filterable by repository,
  contributor, agent, risk, confidence, and free-text search.
- `GET /activity/summary` — aggregate counts (total commits, AI-authored share,
  repositories, review-needed count) for the same filter set.
- `GET /activity/facets` — distinct repositories/contributors/agents, for populating
  filter dropdowns.
- `GET /activity/agents` — per-agent rollup: commit share, repo/contributor coverage,
  certain-vs-suspected attribution split, review-needed count, diff totals, last active.
- `GET /repos/{owner}/{name}/timeline` — same cursor pattern, scoped to one repo.
- `GET /repos/{owner}/{name}/prs/{number}` — single PR detail: pull request row, plus
  its commits, CI runs, and reviews (four separate queries, not a join).

API responsibility stops at data normalization. Formatting, relative timestamps, color/
risk presentation, and grouping are the dashboard's job, not the backend's.

---

## 10. Frontend (React Dashboard)

Stack: React 19, Vite, TypeScript, Tailwind (`@tailwindcss/vite`), TanStack Query.

**Design principle: this is a ledger, not a monitoring dashboard.** Row-based, dense,
typographically-driven layout (see `DESIGN.md`). Achromatic surfaces; color is reserved
for review/reviewed/approved states only, always paired with text/icon, never
color-alone. No auto-refresh reflow — the feed must not jump while someone is reading
it. No gamification (streaks, leaderboards, adoption scores).

**Current implementation (`dashboard/src/components/ActivityFeed.tsx`):**
- **Activity view** — cursor-paginated ledger grouped by day, with filters (repository,
  contributor, agent, risk, confidence) and debounced search. Selecting a row opens an
  **Evidence Inspector** side panel: commit metadata, diff totals, the specific risk
  signals that fired (not just the aggregate level), CI/review state, and a link out to
  GitHub. Summary bar shows AI-authored %, review-needed count, and total commits, with
  an expandable secondary detail row.
- **Agents view** — per-agent breakdown table (share of total commits, repo/contributor
  reach, certain-vs-suspected attribution %, review-needed count, diff totals, last
  active). Clicking an agent returns to the Activity view pre-filtered to that agent —
  there is no separate agents page/product, just a different lens on the same feed.
- The tech-lead view is the superset. The individual-developer view is the same
  component with a contributor filter pre-applied — these are not, and should not
  become, two separate implementations.

**Known gaps against the target:**
- API base URL is hardcoded to `localhost:8000` — needs to become environment-driven
  before this can point at anything but a local backend.
- No GitHub App "Connect" / onboarding flow exists yet in the dashboard — today the only
  way data appears is via manually-sent test webhooks.
- No live/WebSocket updates — the backend has no push mechanism yet, and the frontend
  should not grow WebSocket handling ahead of the backend emitting anything.
- No repo selector/multi-repo navigation beyond the existing activity filter dropdown.

---

## 11. Hard Conventions — Do Not Deviate Without Explicit Discussion

1. Raw SQL via `text()`, not an ORM model layer.
2. `connect_args={"statement_cache_size": 0}` on the async engine — required for
   PgBouncer transaction mode. Never remove.
3. All incoming GitHub timestamps go through a local `parse_dt()` helper
   (`datetime.fromisoformat(value.replace("Z", "+00:00"))`). It's currently duplicated
   per handler file — consolidating it into a shared util is fine, but don't do it
   silently as a side effect of an unrelated change.
4. `database.py` (engine/session) and `db/` (query helpers) intentionally don't share a
   name — this was a prior bug fix. Do not rename `db/` to `database/`.
5. Push webhook commit objects have `author.name`/`author.email` but **no**
   `author.login`. Always use `.get("login")`, never `["login"]`, when reading commit
   author identity from push payloads.
6. Cursor-based pagination for all feed/timeline endpoints — never offset.
7. Idempotent upserts on GitHub's stable IDs for every webhook handler.
8. Windows / Python 3.13 dev environment — be mindful of path separators and shell
   syntax in any commands you suggest running.
9. Schema and infrastructure changes are joint decisions with a collaborator who isn't
   in this workspace — surface the change clearly rather than applying it silently.
10. Don't scaffold v2 risk scoring, WebSocket live-feed, or VS Code extension
    reactivation preemptively — these are deferred by design, not by neglect.

## Non-Goals

- Not a code quality/review tool.
- Not competing with `git-ai` — complementary, reads its data format when present.
- Not tracking inline-suggestion/copy-paste AI usage (Phase 4 attribution) without the
  VS Code extension, which is deferred.
- Not building risk-scoring ML infrastructure until the v1 feed has been validated with
  real users and real data.
