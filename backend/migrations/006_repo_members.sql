-- NOT YET APPLIED. Joint schema decision, sync with DB co-owner before applying. Apply 005 first.

CREATE TABLE repo_members (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    repo_id uuid NOT NULL REFERENCES repos(id),
    supabase_user_id uuid NOT NULL,
    github_login TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'member',
    github_permission TEXT,
    access_checked_at timestamptz NOT NULL,
    access_expires_at timestamptz NOT NULL,
    created_at timestamptz NOT NULL DEFAULT NOW(),
    removed_at timestamptz,
    UNIQUE (repo_id, supabase_user_id)
);

CREATE INDEX repo_members_supabase_user_id_idx
    ON repo_members (supabase_user_id);

ALTER TABLE repo_members ENABLE ROW LEVEL SECURITY;
