-- NOT YET APPLIED. Joint schema decision, sync with DB co-owner before applying. Apply 002-004 first.
-- Links Supabase users (JWT sub) to GitHub App installations for read entitlement.
-- supabase_user_id is intentionally not an FK into Supabase's auth schema -- the app
-- schema must not couple to it, and the backend connects through the pooler as a
-- service role. Membership removed_at gates read access; installations.deleted_at /
-- suspended_at do NOT revoke reads (the audit trail survives removal events).

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
