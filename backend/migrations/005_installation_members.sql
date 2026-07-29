
CREATE TABLE installation_members (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    installation_id uuid NOT NULL REFERENCES installations(id),
    supabase_user_id uuid NOT NULL,
    github_login TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'admin',
    created_at timestamptz NOT NULL DEFAULT NOW(),
    removed_at timestamptz,
    UNIQUE (installation_id, supabase_user_id)
);

CREATE INDEX installation_members_supabase_user_id_idx
    ON installation_members (supabase_user_id);

ALTER TABLE installation_members ENABLE ROW LEVEL SECURITY;
