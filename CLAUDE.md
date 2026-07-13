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
├── main.py                    FastAPI app, webhook signature verification, install guard, event router
├── database.py                async engine + session factory (asyncpg, PgBouncer-safe)
├── auth.py                    require_user() — Supabase JWT verification (HS256 secret or JWKS)
├── github_client.py           shared httpx AsyncClient + retry/backoff, lifespan-closed
├── github_app.py              GitHub App JWT → per-installation access token, cached + locked
├── log_config.py              structured logging setup
├── AttributionResolver.py     git-ai note fetch (enhanced) + heuristic fallback
├── scoring.py                 compute_risk() — flag-count model
├── risk_recompute.py          re-scores a PR's commits when review/CI/linkage changes
├── db/
│   └── repos.py                get_repo(), get_pull_request_id() lookups
├── handlers/
│   ├── Installation.py         handle_installation(), handle_installation_repositories()
│   ├── PullRequests.py         handle_pull_request() + commit backfill + recompute
│   ├── WorkflowRun.py          handle_workflow_run() + recompute
│   ├── PullRequestReview.py    handle_pull_request_review() + recompute
│   └── push.py                 handle_push() — commit ingestion, attribution, scoring
├── routers/
│   ├── activity.py             GET /activity/recent, /summary, /facets, /agents (auth-gated)
│   ├── timeline.py             GET /repos/{owner}/{name}/timeline (auth-gated)
│   └── prs.py                  GET /repos/{owner}/{name}/prs/{number} (auth-gated)
└── migrations/
    ├── 001_v1_schema.sql       full DB schema
    ├── 002_repos_removed_at.sql
    ├── 003_github_app.sql      installations table + repo installation_id linkage
    └── 004_launch_hardening.sql
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
  at push time, then **recomputed** when later review/CI webhooks arrive:
  `risk_recompute.py::recompute_for_pull_request()` is called from both
  `PullRequestReview.py` and `WorkflowRun.py` and updates all PR-linked commits
  (setting `altered_at`). Commits with no PR linkage (e.g. direct-to-main) are never
  recomputed — by design, since no review/CI events reference them.
- RLS is enabled with default-deny (no policies) across all six tables. This closes
  public PostgREST exposure. It does not affect the backend, which connects as a
  `BYPASSRLS` role through the pooler.
- Soft-delete convention: any table representing installable/removable state uses
  soft-delete columns with a `WHERE ... IS NULL` guard on default reads, never hard
  deletes — the audit trail must survive removal events. `repos` uses `removed_at`;
  the `installations` table (added in `003_github_app.sql`) uses `suspended_at` /
  `deleted_at`, set by the `installation` webhook actions (suspend/unsuspend/deleted).

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

**Enhanced mode is now implemented** (was previously stubbed against a non-existent
endpoint). `fetch_git_ai_note()` walks `refs/notes/ai` via the Git Data API the correct
way: ref → notes commit → tree (`?recursive=1`) → find the blob whose path matches the
commit SHA → decode the base64 JSON note. It degrades safely (returns `None`) on any
404/missing-ref/malformed-blob, falling back to the heuristic resolver. `git_ai_model`
is carried through from the note when present.

---

## 6. Risk Scoring (intentionally simple, v1)

`backend/scoring.py::compute_risk()` is an additive flag-count model: 0 flags → low,
1 → medium, 2 → high, 3+ → critical. This is deliberate — there is no real usage data
yet to train or validate anything more sophisticated, and building v2 (Claude Batch API
→ fine-tuned classifier) before v1 has real signal would be premature. Do not scaffold
v2 unless explicitly asked.

**How `risk_no_review` resolves:** `handlers/push.py` still sets `risk_no_review =
True` at ingestion time (reviews arrive later, asynchronously), but
`risk_recompute.py::recompute_for_pull_request()` re-scores a PR's commits whenever a
review, workflow run, or PR-opened/reopened event arrives — so `"low"` is achievable
for any commit that ends up on a reviewed PR. Commits never linked to a PR keep
`risk_no_review = True` permanently, which is the honest claim: they were not reviewed.

---

## 7. GitHub Integration

**Target state:** Flagger is a GitHub App (not a personal-access-token integration).
Installation happens per org/repo through GitHub's install flow, tokens are scoped to
the installation and refreshed automatically, and multiple installations across
different orgs/accounts are tracked and can be soft-removed without losing history.

**Done — the GitHub App token flow is built:**
- `github_app.py`: app JWT (`_make_app_jwt`, RS256, private key from env/path) →
  installation access token via `POST /app/installations/{id}/access_tokens`. Tokens are
  cached per installation with a 5-minute expiry buffer and guarded by a per-installation
  `asyncio.Lock` so concurrent webhooks don't stampede the token endpoint.
- `github_client.py`: one shared `httpx.AsyncClient` with retry/backoff on 5xx/403/429
  (honors `Retry-After`), closed on app shutdown via the lifespan hook.
- `handlers/Installation.py`: `installation` and `installation_repositories` webhooks
  populate the `installations` table and link/unlink `repos.installation_id`.
- `main.py` runs an **installation guard** before dispatching any repo-scoped event:
  untracked/removed repo → ignored; missing/suspended/deleted installation → 409.
- `repo_token(repo)` in `github_app.py` returns the installation token; all handler API
  calls go through it and `github_request`.

**Remaining scaffolding:** `repo_token()` still falls back to a static `GITHUB_TOKEN`
when no App is configured (logs a warning). That fallback is the last PAT-era code path —
new GitHub API calls must use the installation-scoped pattern, never reintroduce a raw
static-token call.

Webhook signature verification (`X-Hub-Signature-256` HMAC check in `main.py`) is
already correct and should remain the first thing that happens on every webhook POST,
before any payload parsing.

---

## 8. Auth & Hosting (partially implemented)

**Done — backend auth:** `auth.py::require_user` verifies a Supabase JWT on every read
router (`/activity/*`, `/repos/*` — wired via `Depends(require_user)` in `main.py`). It
supports both legacy HS256 shared-secret projects (`SUPABASE_JWT_SECRET`) and newer
asymmetric keys via the JWKS endpoint (ES256/RS256), checking `audience` and `issuer`.
`AUTH_DISABLED=true` is a local-dev escape hatch that bypasses verification (it logs a
warning — never set it in a deployed environment). CORS origins are env-driven
(`CORS_ALLOWED_ORIGINS`).

**Done — frontend auth wiring (2026-07-10):** the dashboard has a Supabase client
(`dashboard/src/lib/supabase.ts`, built from `VITE_SUPABASE_URL` + `VITE_SUPABASE_ANON_KEY`;
`null` when unset), `Login.tsx` performs a real GitHub OAuth sign-in via
`supabase.auth.signInWithOAuth`, and `fetchJson` attaches `Authorization: Bearer
<session token>` to every request when the client is configured. When the env vars are
unset (local dev), behavior is unchanged — no header, pair with `AUTH_DISABLED=true`.

**Still open (blocks launch requirement #2 — "only see data you're authorized for"):**
- **Row-level entitlement scoping.** `require_user` proves *who* is calling, but the
  `/activity/*` queries don't yet filter by the caller's authorized installations/orgs —
  a valid token currently sees all data. Per-user data scoping is still required.
- No production hosting decision has been made yet for the backend (API base still
  defaults to `localhost:8000`).

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
- `POST /installations/claim` — links the authenticated user to a GitHub App
  installation after the install redirect (verifies the GitHub OAuth provider token).
- `GET /installations` — the authenticated user's installations, with repo counts.

All read endpoints require a Supabase bearer token and are scoped to the caller's
installation memberships (see §8).

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
- API base is now env-driven (`VITE_API_BASE`, `dashboard/src/lib/api.ts`), defaulting to
  `localhost:8000` — set it in the deploy environment to point at a real backend.
- `Connect`, `Repositories`, and `Settings` components now exist; the dashboard is no
  longer activity-feed-only. `Connect`'s install link is env-driven
  (`VITE_GITHUB_APP_INSTALL_URL`; falls back to the GitHub Apps directory until the real
  App slug exists). The onboarding flow still needs installation-state reflection, not
  just facet reads.
- `fetchJson` attaches the Supabase session token when configured — see §8. Build is
  `tsc -b && vite build` (typecheck enforced).
- No live/WebSocket updates — the backend has no push mechanism yet, and the frontend
  should not grow WebSocket handling ahead of the backend emitting anything.

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

## 12. Launch Status — Done / Next

Snapshot of where the build stands against the launch criteria in §2. Update this
section as items move.

**Done since v1 schema:**
- GitHub App token flow — installation JWT → cached, per-installation-locked access
  tokens (`github_app.py`), shared retrying httpx client (`github_client.py`). Replaces
  the static-PAT path (a fallback remains, §7).
- `installations` table + `installation`/`installation_repositories` webhooks, with
  suspend/unsuspend/delete soft-delete and repo linkage (`003_github_app.sql`).
- Webhook installation guard in `main.py` — ignores untracked repos, 409s on
  missing/suspended/deleted installs before any handler runs.
- git-ai enhanced attribution actually implemented via the Git Data API ref-walk (§5).
- Backend auth — Supabase JWT verification on all read routers (`auth.py`), env-driven
  CORS, `AUTH_DISABLED` dev escape hatch.
- Dashboard API base is env-driven; `Connect`/`Repositories`/`Settings` views added.
- `004_launch_hardening.sql` applied.

**Next (ordered roughly by launch impact):**
1. ~~Frontend auth wiring~~ **Done (2026-07-10)** — Supabase GitHub OAuth in `Login.tsx`
   and `fetchJson` sends `Authorization: Bearer <token>` when `VITE_SUPABASE_URL`/
   `VITE_SUPABASE_ANON_KEY` are set (§8).
2. **Row-level entitlement scoping** — filter `/activity/*` and `/repos/*` by the
   caller's authorized installations/orgs; a valid token currently sees all data (§8).
   This is launch requirement #2.
3. ~~Make `"low"` risk reachable~~ **Done for PR-linked commits** (verified end-to-end
   2026-07-09, see §13.5): review ingestion now works and recompute produces `"low"`.
   `risk_no_review` is still hardcoded `True` at push time (§6), so the remaining gap
   is only commits that never get a PR/review.
4. ~~Recompute risk on later review/CI events~~ **Done** — `risk_recompute.py`, called
   from the review and workflow handlers (§4, §13.17).
5. **GitHub App onboarding flow** — install URL is now env-driven
   (`VITE_GITHUB_APP_INSTALL_URL`, 2026-07-10); still needs the real App slug and
   installation-state reflection in `Connect`, not just facet reads (§10).
6. **Backend hosting** — no production hosting decision yet; API base still defaults to
   `localhost:8000` (§8).

Deferred by design (do not build ahead of need): v2 risk scoring, WebSocket live feed,
VS Code extension (§11.10).

## 13. Known Bugs — Live Run-Through (2026-07-09)

Found by driving the running app (backend + dashboard, Playwright) plus two independent
code reviews (Claude subagent + Codex). "Live" = reproduced against the running app;
"code" = confirmed by reading the code; "suspected" = strong evidence, not reproduced.

**Backend**
1. **FIXED (2026-07-09)** *(was live)* Malformed `cursor` (any non-UUID) → **500** on
   `/activity/recent` and `/repos/{o}/{n}/timeline`; timeline also 500'd on a
   valid-but-unknown UUID cursor. Fix: both routers validate the cursor with
   `UUID(cursor)` and treat invalid values as "no cursor" (first page), and timeline
   gained the same `cursor_timestamp is not None` guard activity already had.
   Verified live: malformed/unknown cursors return 200 first pages; valid pagination
   round-trips unchanged. Codex-reviewed: correct as-is.
2. **FIXED (2026-07-09)** *(was code)* `timeline.py` `ORDER BY pushed_at DESC` lacked
   the `id DESC` tiebreaker its `(pushed_at, id)` cursor assumes — same-timestamp
   commits could be skipped/duplicated across pages. Fix: added `commits.id DESC`,
   matching `activity.py`.
3. **FIXED (2026-07-10)** *(was code)* No router filtered `repos.removed_at IS NULL`.
   Fix: `activity.py::activity_filters` seeds the clause unconditionally (covers
   `/recent` + `/summary`); `/facets` and `/agents` gained the WHERE (and `/agents` the
   missing repos join). Timeline/PR detail were already covered via `get_repo()`.
4. **FIXED (2026-07-10)** *(was code)* Webhook race: `get_pull_request_id()` 404'd when
   a review/workflow_run event arrived before the PR row existed, losing the event.
   Fix: PR upsert extracted to `PullRequests.py::upsert_pull_request()`;
   `get_pull_request_id(..., required=False)` returns `None` instead of raising;
   `PullRequestReview.py` creates the missing PR from the webhook's full
   `pull_request` object, `WorkflowRun.py` fetches the PR from the GitHub API
   (installation token) and upserts it, logging + skipping (no 500) if the fetch fails.
   Workflow runs with an empty `pull_requests` list are still skipped by design
   (schema requires a PR), now with a log line.
5. **CONFIRMED & FIXED (2026-07-09)** *(was suspected)* `PullRequestReview.py` read
   `review["created_at"]`, which GitHub's review webhook object does not include (only
   `submitted_at`) → KeyError/500 on every review webhook; this is why the DB had zero
   reviews. Fix: `review.get("created_at") or review["submitted_at"]`. Verified
   end-to-end with a signed `pull_request_review` webhook (no `created_at` key):
   200, review row inserted, and `risk_recompute` flipped the PR's commit from
   `medium` → `low` — proving launch requirement #4 ("low" reachable) works once
   reviews ingest. (`submitted_at` is absent only on PENDING reviews, which never
   fire this webhook.) Codex-reviewed: correct as-is.
6. **FIXED (2026-07-10)** *(was code)* PR upsert's `ON CONFLICT` now also updates
   `title`, `url`, `author_login` — `edited` events no longer leave stale metadata.
7. **FIXED (2026-07-10)** *(was code)* `AttributionResolver.py` co-author check now uses
   `re.finditer` over **all** `Co-authored-by:` trailers — a human co-author listed
   before the agent no longer hides the agent.
8. **FIXED (2026-07-10)** *(was code)* Definition drift resolved: push-time
   `risk_large_unreviewed` is now `additions > 500 AND no_review` (`push.py`), matching
   `risk_recompute.py` (identical value at push time while `risk_no_review` is
   hardcoded `True` there, but the flag now means one thing).

**Frontend**
9. **FIXED (2026-07-10)** *(was live)* "Review queue" sort scrambled day groups. Fix:
   commits are sorted by `pushed_at` desc first, day groups built from that order
   (newest day always first), then priority sort applied *within* each group. The sort
   still only applies to the loaded page — inherent to server-side pagination, accepted.
10. **FIXED (2026-07-10)** *(was live)* Ledger row title and its aria-label now render
    only the first line of the commit message — `Co-authored-by:` trailers no longer
    leak into the feed.
11. **FIXED (2026-07-10)** *(was live)* PR detail view is now reachable: feed/timeline
    queries LEFT JOIN `pull_requests` to expose `pr_number`, and the Evidence Inspector
    links to `#/repos/{owner}/{repo}/pr/{n}` when the commit belongs to a PR.
12. **FIXED (2026-07-10)** *(was code)* Pagination cursor reset moved to a single
    `useEffect` on `filters` in `ActivityFeed` — every filter change (topbar search,
    Repositories "View activity", "Clear filters", in-component filters) now resets the
    cursor through one path; the per-call resets in `updateFilter` were removed.
13. **FIXED (2026-07-10)** *(was code)* Summary chips render `—` on fetch error instead
    of fake zeros (`data-populated` also stays false on error). The duplicate loading
    card was removed; `isPending` renders only the skeleton.
14. **FIXED (2026-07-10)** *(was code)* `Repositories.tsx` renders a neutral `—` cell
    (no state class) while a per-repo summary is in flight, instead of green "Clear".
15. **FIXED (2026-07-10)** *(was code)* Both onboarding CTAs are real now: `Connect.tsx`
    install link is env-driven (`VITE_GITHUB_APP_INSTALL_URL`, generic directory +
    "App slug pending" title only as fallback), and `Login.tsx` performs Supabase
    GitHub OAuth when configured (see §8), falling back to plain navigation in local
    dev with no Supabase env.
16. **FIXED (2026-07-10)** *(was suspected)* Strict-null violations resolved (summary
    stats are plain `number` now) and `build` is `tsc -b && vite build`, so the
    typecheck is enforced; `*.tsbuildinfo` gitignored. One latent unused-variable error
    surfaced by `tsc -b` was removed.

**Stale docs (this file)**
17. **FIXED (2026-07-10)** — §8, §10, and §12 updated to reflect frontend auth wiring,
    the env-driven install URL, and the fixes above.

Previously noted here and now resolved: `fetchJson` sends the Supabase session token
when configured (§8). Still open: per-user entitlement scoping — any valid token reads
all data (§12 Next #2).

## Non-Goals

- Not a code quality/review tool.
- Not competing with `git-ai` — complementary, reads its data format when present.
- Not tracking inline-suggestion/copy-paste AI usage (Phase 4 attribution) without the
  VS Code extension, which is deferred.
- Not building risk-scoring ML infrastructure until the v1 feed has been validated with
  real users and real data.
