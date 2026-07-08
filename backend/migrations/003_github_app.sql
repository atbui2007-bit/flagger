-- NOT YET APPLIED. Joint schema decision, sync with DB co-owner before applying. Apply 002 then 003. repos.webhook_secret is planned for deprecation once the GitHub App webhook secret (single app-level secret) fully replaces per-repo secrets; do not drop it in this migration.

CREATE TABLE installations (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    github_installation_id BIGINT UNIQUE NOT NULL,
    account_login TEXT NOT NULL,
    account_type TEXT,
    installed_at timestamptz NOT NULL DEFAULT NOW(),
    suspended_at timestamptz,
    deleted_at timestamptz
);

ALTER TABLE repos
ADD COLUMN installation_id uuid REFERENCES installations(id);

ALTER TABLE installations ENABLE ROW LEVEL SECURITY;
