# CLAUDE.md — Flagger

This is the canonical context file for Claude Code in this repo. Read it before making
changes. It describes what Flagger is, what shipped in v1 (launched), and what v2 is
about. It does not contain a task list — task tracking lives in Notion. Treat the
conventions below as deliberate, not default scaffolding to "clean up."

---

If the Codex Plugin is installed, implement code with codex and consult with Codex 5.6 Sol on the task at hand.

## 1. What Flagger Is

Flagger is an **audit-trail SaaS product** for engineering teams adopting AI coding
agents. It answers one question for a tech lead: *"Everything AI touched in this repo —
show it to me, ordered, traceable, in one place."* A secondary, not-yet-validated
question is which of that activity actually needs attention before it ships (risk
scoring, intentionally simple in v1).

Flagger is **not** a code quality reviewer — that's CodeRabbit's job. It tracks
provenance and process (who/what wrote code, how much oversight it got), not whether the
code is good.

**Differentiator:** zero developer-side setup. Competing tools like `git-ai` require a
CLI wrapper per developer. Flagger connects via a GitHub App webhook once, at the repo
level, and gets visibility immediately. Flagger treats `git-ai` as complementary, not a
competitor: if a repo has `git-ai` Git Notes at `refs/notes/ai`, Flagger reads them as a
higher-confidence attribution source; otherwise it falls back to its own heuristics.

**Primary users:** tech leads / staff engineers wanting a cross-repo, cross-contributor
view of AI-authored activity, with budget authority.
**Secondary users:** individual developers reviewing their own agent activity — the same
feed, scoped with a contributor filter. There is one view, not two products.

**Brand/product feel** (see `DESIGN.md` for full tokens): "The Ledger Under Glass" —
dark-first, glass-forward, premium. Every container is a rounded frosted-glass panel
over a composed wallpaper-grade gradient canvas; dense data rows sit on a high-opacity
tint inside the glass so evidence stays crisp (blur belongs to panel shells only, never
rows, never nested). All data and columns stay — premium comes from material and
spacing, not from hiding information. Minimal token-driven motion (DESIGN.md §5);
imperceptibly drifting canvas (transform-only, ≥100s cycles, frozen under reduced
motion). Explicitly not a Datadog-style observability wall, no gamification, no
color-only risk signals, no feed reflow on live updates, no perceptible background
motion.

---

## 2. v1 — Launched

Flagger v1 is live: backend on Railway (`backend/Dockerfile` + `backend/railway.json`,
runbook in `backend/DEPLOY.md`), dashboard on Vercel, real GitHub App created with its
slug in `VITE_GITHUB_APP_INSTALL_URL`, Supabase GitHub OAuth enabled (auth verified
end-to-end 2026-07-14), migrations 001–005 applied to production. An external user can
install the App with zero CLI/config, sign in, and see a correctly-scoped activity feed
with honest attribution confidence and reachable "low" risk.

### Architecture

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

Monorepo: `backend/` (FastAPI), `dashboard/` (React 19 + Vite + TypeScript + Tailwind +
TanStack Query), `extension/` (VS Code — deferred, not active development).

Backend file map:

```
backend/
├── main.py                    FastAPI app, webhook signature verification, install guard, event router
├── database.py                async engine + session factory (asyncpg, PgBouncer-safe)
├── auth.py                    require_user() — Supabase JWT verification; entitlement_filter()
├── github_client.py           shared httpx AsyncClient + retry/backoff, lifespan-closed
├── github_app.py              GitHub App JWT → per-installation access token, cached + locked
├── log_config.py              structured logging setup
├── AttributionResolver.py     git-ai note fetch (enhanced) + heuristic fallback
├── scoring.py                 compute_risk() — flag-count model
├── risk_recompute.py          re-scores a PR's commits when review/CI/linkage changes
├── db/repos.py                get_repo(), get_pull_request_id() lookups
├── handlers/                  Installation, PullRequests, WorkflowRun, PullRequestReview, push
├── routers/
│   ├── activity.py            GET /activity/recent, /summary, /facets, /agents
│   ├── timeline.py            GET /repos/{owner}/{name}/timeline
│   ├── prs.py                 GET /repos/{owner}/{name}/prs/{number}
│   └── installations.py       POST /installations/claim, GET /installations
└── migrations/                001_v1_schema … 005_installation_members (all applied)
```

### Database

Six core tables (`001_v1_schema.sql`): `repos` → `commits` → `file_changes`;
`commits.pull_request_id` (nullable, inferred at push time from open PR on
`repo_id`+`head_branch`) → `pull_requests` → `ci_runs`, `reviews`. Plus
`installations` (003) and `installation_members` (005). RLS enabled default-deny on
all tables (backend connects as a `BYPASSRLS` role through the pooler). Soft-delete
everywhere state is removable (`repos.removed_at`, `installations.suspended_at`/
`deleted_at`, `installation_members.removed_at`) — the audit trail must survive
removal events; default reads guard with `WHERE ... IS NULL`.

### Attribution

Two-mode resolver (`AttributionResolver.py`): **enhanced** — `git-ai` Git Notes at
`refs/notes/ai` read via the Git Data API ref-walk (ref → notes commit → recursive
tree → blob matching the commit SHA → base64 JSON note), `attribution_source =
"git_ai_notes"`, `confidence = "certain"`, degrades safely to `None` on any miss;
**heuristic fallback** — bot-account login matching, `Co-authored-by:` trailer parsing
(all trailers, via `re.finditer`), else `agent_type = "unknown"`, `confidence =
"suspected"`. Confidence is always surfaced explicitly in the UI — "Devin (certain)"
and "Heuristic match (suspected)" are different claims; never flatten them.

Agent coverage is phased: Phase 1 (shipped) — Claude Code, Codex, Devin, Aider.
Phase 2+ (Lovable, Replit, Cursor Agent, Copilot Agent) and Phase 4 (inline
suggestions, needs the VS Code extension) are out of scope until Phase 1 is validated.

### Risk scoring

`scoring.py::compute_risk()` — additive flag count (0 → low, 1 → medium, 2 → high,
3+ → critical) over `risk_no_review`, `risk_ci_unclean`, `risk_sensitive_path`,
`risk_large_unreviewed` (`additions > 500 AND no_review`), `risk_direct_to_main`.
Computed at push time (`risk_no_review` starts `True` — reviews arrive later), then
**recomputed** by `risk_recompute.py::recompute_for_pull_request()` whenever a review,
workflow run, or PR event lands — so "low" is reachable for any commit that ends up on
a reviewed PR. Commits never linked to a PR keep `risk_no_review = True` permanently,
which is the honest claim. Deliberately simple; v2 ML scoring is deferred until real
usage data exists.

### GitHub integration

Flagger is a GitHub App. `github_app.py`: app JWT (RS256) → installation access token
(`POST /app/installations/{id}/access_tokens`), cached per installation with a
5-minute expiry buffer, per-installation `asyncio.Lock` against token stampedes.
`github_client.py`: one shared `httpx.AsyncClient` with retry/backoff on 5xx/403/429
(honors `Retry-After`), closed via lifespan hook. `repo_token(repo)` returns an
installation-scoped token or **raises** — the PAT era is fully gone; never reintroduce
a static-token call. Webhook signature verification (`X-Hub-Signature-256` HMAC in
`main.py`) is the first thing that happens on every webhook POST, before any payload
parsing; then the installation guard (untracked/removed repo → ignored,
missing/suspended/deleted installation → 409) runs before any handler.

### Auth & entitlements

`auth.py::require_user` verifies the Supabase JWT on every read router (HS256 shared
secret or JWKS ES256/RS256; checks audience + issuer). `AUTH_DISABLED=true` is a
local-dev-only escape hatch. Every read query is scoped by
`auth.py::entitlement_filter` — an IN-subquery on `commits.repo_id` over the caller's
active `installation_members` rows. `get_repo` 404s (not 403) for unentitled repos to
avoid existence leaks. `POST /installations/claim` links a signed-in user to an
installation after the App install redirect: verifies the GitHub OAuth
`provider_token` belongs to the JWT's GitHub identity (`GET /user` vs
`user_metadata.provider_id`), checks the installation appears in
`GET /user/installations`, then idempotently upserts installation + membership
(role `admin`). The dashboard (`lib/auth.tsx`) owns session state, stashes
`provider_token` in sessionStorage at OAuth redirect, captures the App Setup redirect
before React renders, and claims it in `Connect.tsx`; 401s sign the user out.

### Backend API

- `POST /webhook` — single endpoint, event type from `X-GitHub-Event`, signature-verified, dispatched to `handlers/`.
- `GET /activity/recent` — cursor-paginated commit feed (repository, contributor, agent, risk, confidence, search filters).
- `GET /activity/summary`, `/facets`, `/agents` — aggregates, filter options, per-agent rollup for the same filter set.
- `GET /repos/{owner}/{name}/timeline` — same cursor pattern, one repo.
- `GET /repos/{owner}/{name}/prs/{number}` — PR detail (four separate queries, not a join — joins would multiply rows).
- `POST /installations/claim`, `GET /installations` — see auth above.

All read endpoints require a Supabase bearer token and are entitlement-scoped. API
responsibility stops at data normalization — formatting, relative timestamps, risk
presentation, and grouping are the dashboard's job.

### Frontend

One view, two lenses: the **Activity** ledger (cursor-paginated, grouped by day,
filters + debounced search, Evidence Inspector side panel with per-signal risk
breakdown and GitHub/PR links) and the **Agents** table (per-agent share, reach,
certain-vs-suspected split — clicking an agent just pre-filters the Activity view).
`Connect`/`Repositories`/`Settings` handle onboarding and installation state. The
individual-developer view is the same component with a contributor filter — never two
implementations. Env-driven config: `VITE_API_BASE` (Railway URL in prod),
`VITE_SUPABASE_URL`/`VITE_SUPABASE_ANON_KEY`, `VITE_GITHUB_APP_INSTALL_URL`. Build is
`tsc -b && vite build` (typecheck enforced). No live/WebSocket updates — the backend
has no push mechanism; don't grow one ahead of it.

v1 also closed a 17-item launch bug ledger (cursor-validation 500s, webhook
race/ordering fixes, review ingestion KeyError, co-author trailer leaks, pagination
reset unification, honest loading/error states — all verified live 2026-07-09/10).
Details live in git history if ever needed.

---

## 3. Hard Conventions — Do Not Deviate Without Explicit Discussion

1. Raw SQL via `text()`, not an ORM model layer. The schema was designed in SQL first.
2. `connect_args={"statement_cache_size": 0}` on the async engine — required for
   PgBouncer transaction mode (no prepared statements). Never remove.
3. All incoming GitHub timestamps go through a local `parse_dt()` helper
   (`datetime.fromisoformat(value.replace("Z", "+00:00"))`). It's duplicated per
   handler file — consolidating it is fine, but not silently as a side effect of an
   unrelated change.
4. `database.py` (engine/session) and `db/` (query helpers) intentionally don't share
   a name — prior bug fix. Do not rename `db/` to `database/`.
5. Push webhook commit objects have `author.name`/`author.email` but **no**
   `author.login`. Always `.get("login")`, never `["login"]`.
6. Cursor-based pagination (`(pushed_at, id)` tuple comparison) for all feed/timeline
   endpoints — never offset.
7. Idempotent upserts on GitHub's stable IDs (`github_pr_number`+`repo_id`,
   `github_run_id`, `github_review_id`, commit `sha`) for every webhook handler —
   GitHub redelivers webhooks.
8. SQLAlchemy `Row` objects must be converted with `dict(row._mapping)` before FastAPI
   can serialize them — this has bitten every new endpoint; do it proactively.
9. Windows / Python 3.13 dev environment — mind path separators and shell syntax.
10. Schema and infrastructure changes are joint decisions with a DB collaborator who
    isn't in this workspace — surface migrations clearly, never apply silently.
11. Soft-delete convention: removable state gets a `removed_at`-style column and a
    `WHERE ... IS NULL` guard on default reads, never hard deletes.
12. Don't scaffold v2 ML risk scoring, WebSocket live-feed, or VS Code extension
    reactivation preemptively — deferred by design, not by neglect.

---

## 4. v2 — Current Focus: Contributor Access

**Status (2026-07-19): shipped and verified live.** Migration 006 applied to
production; backend (`/installations/sync-access`, UNION'd `entitlement_filter`,
`get_repo`, membership-aware `GET /installations`) and dashboard (app-boot sync in
`App.tsx`, reconnect action in `Settings.tsx`) deployed. E2E-verified 2026-07-19: a
collaborator (non-installer) signed in and received correctly scoped repo access via
sync — the provider_token and `/user/installations` assumptions hold in production.
Outside-collaborator-on-private-repo remains the one edge from the "verify live"
list not yet exercised.

**Problem:** v1 entitlement is installation-level, and the only path into
`installation_members` is `POST /installations/claim`, driven by the App install
redirect — a flow only the installer (org owner / repo admin) ever goes through. A
contributor/collaborator on the same repos has no way to see any Flagger data, even
though GitHub itself grants them access to those repos.

**Goal:** a signed-in user who is a collaborator on repos covered by an existing
Flagger installation gets appropriately scoped access without a new installation.

**Design (consulted with Codex, 2026-07-17 — verify the flagged items live before
building):**

- **GitHub primitives:** `GET /user/installations` (user OAuth token) lists
  installations the user has explicit access to — including via repo collaboration,
  not just ownership/org membership. `GET /user/installations/{id}/repositories`
  returns exactly the subset of that installation's repos the user can access, with
  per-repo `permissions`. Grant from the per-repo endpoint, never installation-wide
  from the first endpoint alone.
- **Schema delta (migration 006 — flag to the DB collaborator before applying):** new
  `repo_members` table — `(repo_id, supabase_user_id)` unique, `github_login`,
  `role` default `'member'`, `github_permission`, `access_checked_at`,
  `access_expires_at`, `removed_at` soft delete, RLS enabled. A separate table, not a
  nullable repo scope on `installation_members` — installation-wide admin grants and
  repo-scoped collaborator grants are different things and a nullable scope column is
  easy to get wrong in the entitlement predicate.
- **Endpoint:** `POST /installations/sync-access` — same identity binding as claim
  (provider token must match the JWT's GitHub id), walks `GET /user/installations`,
  intersects with tracked installations, walks each
  `/user/installations/{id}/repositories`, intersects with tracked repos, upserts
  `repo_members` rows (`role='member'`, `access_expires_at = NOW() + 24h`), and
  soft-removes grants no longer returned. Dashboard calls it after sign-in/session
  restore.
- **Entitlement predicate:** `entitlement_filter` becomes a UNION of the existing
  `installation_members` subquery and a `repo_members` subquery
  (`removed_at IS NULL AND access_expires_at > NOW()`), still one composable
  IN-predicate, one round-trip.
- **Revocation:** TTL + re-sync on session start. No webhook-driven revocation —
  collaborator add/remove isn't cleanly observable with our App permissions, and
  bounded staleness (24h TTL) is acceptable for v2's first cut.
- **Roles:** `admin` (installation-wide, from claim) vs `member` (repo-scoped, from
  sync). Role gates nothing yet beyond which table grants the row — metadata until an
  admin-only action exists.
- **`GET /installations`** gains repo-membership-reachable installations, with repo
  counts scoped to what the caller can actually see.

**Verify live before building** (Codex flagged these as untested edge behavior):
1. `GET /user/installations` includes an org installation when the user is only an
   outside collaborator on one private repo.
2. `/user/installations/{id}/repositories` returns the collaborator-visible subset for
   both `all` and `selected` repository_selection.
3. Supabase's `provider_token` works against these endpoints (the claim flow already
   depends on this assumption and was verified 2026-07-14, so likely fine).

Deferred by design (do not build ahead of need): v2 ML risk scoring, WebSocket live
feed, VS Code extension.

---

## 5. Known-Bugs Ledger (from the 2026-07-19 four-agent review)

A full review (2 Claude subagents + 2 Codex tasks: backend correctness, new-user
walkthrough, dashboard bug hunt, security) ran 2026-07-19. The "this week" slice
shipped the same night (commit `1fab4b8` + migration 007): claim privilege-escalation
fix, `AUTH_DISABLED` production gate, merge-commit→PR linking, >20-commit push
backfill, ID-keyed webhook guard with rename self-heal, payload debug-log removal.
Everything below is **found, verified, and still open** — ranked within each group.
Details (exact failure scenarios, line refs) are in the session reports; SQL injection
was audited clean (all user input parameterized).

### Security (this month)

1. Installation-wide `installation_members` grants never expire or revalidate —
   `sync-access` refreshes only `repo_members`. A user removed from an org keeps full
   read access until someone manually sets `removed_at`. Add TTL/revalidation.
2. `provider_token` lives in sessionStorage (`lib/auth.tsx`) — XSS or a hostile
   extension steals a live GitHub OAuth token. Mitigations, in order: CSP + security
   headers (none exist today, cheapest win), then server-side token handling.
3. RLS: enabled on only `installations`/`installation_members`/`repo_members`, no
   policies anywhere, nothing on `repos`/`commits`/`pull_requests`/`ci_runs`/
   `reviews`/`file_changes`. Zero DB-level tenant isolation if the API layer slips.
   (Schema work — DB collaborator decision.)
4. Commit/PR URLs from ingestion render as anchors unvalidated — restrict to
   `https://github.com/...` at ingest or serialization.
5. Cursor commit-id lookup in `activity.py`/`timeline.py` is unscoped by entitlement
   (timestamp-ordering oracle only; reuse the entitlement predicate in the lookup).

### Data correctness (risk claims must be honest)

6. `risk_ci_unclean` is a ratchet: one failed run keeps every commit on the PR
   flagged after a passing rerun (`risk_recompute.py` EXISTS over all `ci_runs`).
   Should consider only the latest run per workflow/check.
7. `WorkflowRun.py` attaches CI to `pull_requests[0]` only — sibling PRs on the same
   branch never get CI signals; fork-head runs get none (payload list is empty).
8. Aider attribution never fires: case-sensitive `startswith("Aider")` vs lowercase
   `aider` trailers (`AttributionResolver.py`). Compare case-insensitively; also
   verify the hardcoded `claude-ai[bot]` login against reality.
9. Failed commit-diff fetch silently zeroes additions/risk inputs (`push.py`) — a
   GitHub blip permanently understates risk with no flag. Also: REST `files` caps at
   300; use the response's `stats` totals for additions/deletions.
10. `github_client.py` retry: HTTP-date `Retry-After` crashes (`float()` ValueError →
    webhook 500); numeric values sleep unbounded mid-webhook; plain 403s retry
    pointlessly. Cap the sleep, parse both formats, skip retry on non-rate-limit 403.
11. `timeline.py` `limit` lacks `ge=1` — `limit=0` → 500 (IndexError), negative →
    SQL error. Copy the `activity.py` pattern.
12. Deleted "ghost" accounts 500 webhooks: `pr["user"]["login"]` /
    `review["user"]["login"]` on `user: null` (`PullRequests.py`,
    `PullRequestReview.py`).
13. Dismissed reviews still satisfy `has_review` (`risk_recompute.py` doesn't filter
    state), so "no review" clears on a dismissed-only PR.
14. Tag pushes aren't filtered (`push.py`): `refs/tags/v1` becomes `branch` verbatim
    with wrong direct-to-main semantics.
15. A webhook 500 loses the event permanently (GitHub doesn't auto-redeliver), and
    big pushes (~100 sequential API calls) will exceed GitHub's 10s delivery timeout
    — consider ack-then-process or at least tightening per-delivery work.

### Dashboard / first-run UX (this month — these lose new users)

16. Signed-in user with zero installations lands on Activity and sees "✓ All clear"
    + "No activity matches these filters / Clear filters" — every message wrong; the
    page needs a real not-connected empty state pointing at Connect.
17. Freshly installed repos are invisible until their first push — facets and
    `Repositories.tsx` build from `commits`, contradicting "takes under a minute to
    appear". List repos from the `repos` table instead.
18. Connect claim traps: wrong-GitHub-account claim shows raw "Request failed: 403"
    with an eternal Retry and the pending id re-fires every reload (no dismiss path);
    expired-but-present provider_token hits the same dead Retry because backend maps
    GitHub 401→403 and `needsReauth` only checks token *absence*.
19. Any API 401 silently signs the user out mid-session with no message
    (`lib/api.ts`); a JWT misconfig becomes an infinite login loop. Show a
    "session expired" state.
20. `accessSyncStarted` is a module-level flag never reset on sign-out (`App.tsx`) —
    user B on the same tab never syncs; `provider_token` is per-tab sessionStorage so
    new tabs/restarts silently skip sync until repo grants TTL out with no visible
    remedy outside Settings. Also surface sync failure on the Activity page itself.
21. `queryClient` cache isn't cleared on sign-out — next account briefly sees the
    previous account's data.
22. Feed mechanics: double-click Next corrupts `cursorHistory`; filter changes race
    the stale cursor for one render (query key uses new filters + old cursor);
    `Number(attribution_confidence)` is NaN so confidence never affects the
    review-queue sort; search doesn't escape `%`/`_`; Evidence Inspector stays open
    showing a stale commit across pagination; no `placeholderData` so every page
    flips to skeleton.
23. OAuth `redirectTo: location.origin` drops the hash — shared deep links (e.g. a
    PR URL) never survive sign-in; denied OAuth (`error=access_denied`) lands on
    Login with zero explanation; `setup_action=request` (org-approval flow) is
    dropped by `main.tsx` so the user sees an unexplained empty dashboard.

### Backlog (real, not urgent)

24. `GET /installations` claim-status polish: `status: "member"` responses from the
    hardened claim aren't surfaced distinctly in Connect yet ("connected as member"
    vs "connected as admin").
25. `completed_at` on in-flight workflow runs shows `updated_at` until completion.
26. NULL `pushed_at` commits (latent) would sort first and break pagination — guard
    when mapping `commit["timestamp"]`.
27. Greeting hour captured once ("Good morning." all afternoon); light-theme users
    get a dark first paint (`data-theme` set in an effect).

---

## Non-Goals

- Not a code quality/review tool.
- Not competing with `git-ai` — complementary, reads its data format when present.
- Not tracking inline-suggestion/copy-paste AI usage (Phase 4 attribution) without the
  VS Code extension, which is deferred.
- Not building risk-scoring ML infrastructure until the v1 feed has been validated with
  real users and real data.
