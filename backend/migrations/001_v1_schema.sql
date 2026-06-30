CREATE TABLE repos (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    github_repo_id INT UNIQUE NOT NULL,
    owner TEXT NOT NULL,
    name TEXT NOT NULL,
    full_name TEXT NOT NULL,
    default_branch TEXT NOT NULL,
    webhook_secret TEXT NOT NULL,
    attribution_mode TEXT NOT NULL DEFAULT 'heuristic',
    installed_at timestamptz DEFAULT NOW()
);
CREATE TABLE pull_requests (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    repo_id uuid NOT NULL REFERENCES repos(id),
    head_branch TEXT,
    github_pr_number INT NOT NULL,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    author_login TEXT NOT NULL,
    state TEXT NOT NULL,
    merged_at timestamptz,
    created_at timestamptz NOT NULL,
    updated_at timestamptz NOT NULL,
    closed_at timestamptz,
    UNIQUE (github_pr_number, repo_id)
);
CREATE TABLE commits (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    repo_id UUID NOT NULL REFERENCES repos(id),
    pull_request_id UUID REFERENCES pull_requests(id),
    sha TEXT UNIQUE NOT NULL,
    short_sha TEXT NOT NULL,
    message TEXT NOT NULL,
    url TEXT NOT NULL,
    branch TEXT NOT NULL,
    merged_to_default boolean NOT NULL DEFAULT false,
    agent_type TEXT NOT NULL,
    attribution_source TEXT NOT NULL,
    attribution_confidence TEXT NOT NULL,
    attribution_signal TEXT NOT NULL,
    author_login TEXT NOT NULL,
    author_avatar_url TEXT,
    git_ai_model TEXT,
    github_ai_summary_prompt TEXT,
    github_ai_approved_lines INT,
    github_ai_overridden_lines INT,
    additions INT DEFAULT 0,
    deletions INT DEFAULT 0,
    risk_level TEXT,
    risk_no_review boolean NOT NULL DEFAULT true,
    risk_ci_unclean boolean NOT NULL DEFAULT false,
    risk_sensitive_path boolean NOT NULL DEFAULT false,
    risk_large_unreviewed boolean NOT NULL DEFAULT false,
    risk_direct_to_main boolean NOT NULL DEFAULT false,
    pushed_at timestamptz NOT NULL,
    arrived_at timestamptz NOT NULL,
    altered_at timestamptz
);
CREATE TABLE file_changes (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    commit_id UUID NOT NULL REFERENCES commits(id),
    file_path TEXT NOT NULL,
    change_type TEXT,
    additions INT DEFAULT 0,
    deletions INT DEFAULT 0,
    ai_lines_ranges jsonb
);
CREATE TABLE ci_runs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    pull_request_id UUID NOT NULL REFERENCES pull_requests(id),
    github_run_id bigint UNIQUE NOT NULL, 
    workflow_name TEXT NOT NULL,
    status TEXT NOT NULL,
    conclusion TEXT,
    started_at timestamptz NOT NULL,
    completed_at timestamptz,
    created_at timestamptz NOT NULL
);
CREATE TABLE reviews (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    pull_request_id UUID NOT NULL REFERENCES pull_requests(id),
    github_review_id bigint UNIQUE NOT NULL,
    reviewer_login TEXT NOT NULL,
    state TEXT NOT NULL,
    submitted_at timestamptz NOT NULL,
    created_at timestamptz NOT NULL
);
    CREATE INDEX ON commits (pull_request_id);
    CREATE INDEX ON file_changes (commit_id);
    CREATE INDEX ON file_changes (file_path);
    CREATE INDEX ON reviews (pull_request_id);
    CREATE INDEX ON commits (repo_id);
    CREATE INDEX ON commits (agent_type);
    CREATE INDEX ON commits (risk_level);
    CREATE INDEX ON ci_runs (pull_request_id);