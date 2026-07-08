-- NOT YET APPLIED. Joint schema decision, sync with DB co-owner before applying. Apply 002, then 003, then 004.

ALTER TABLE repos ALTER COLUMN github_repo_id TYPE bigint;

ALTER TABLE repos ALTER COLUMN webhook_secret SET DEFAULT '';  -- unblocks auto-provisioning inserts; column kept per deprecation plan

ALTER TABLE repos ADD COLUMN created_at timestamptz NOT NULL DEFAULT NOW();
ALTER TABLE repos ADD COLUMN updated_at timestamptz NOT NULL DEFAULT NOW();
ALTER TABLE file_changes ADD COLUMN created_at timestamptz NOT NULL DEFAULT NOW();
ALTER TABLE file_changes ADD COLUMN updated_at timestamptz NOT NULL DEFAULT NOW();

CREATE INDEX ON commits (pushed_at DESC, id DESC);
CREATE INDEX ON commits (author_login);
CREATE INDEX ON commits (LOWER(attribution_confidence));
CREATE INDEX ON commits (repo_id, branch);

CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE INDEX ON commits USING GIN (message gin_trgm_ops);
CREATE INDEX ON commits USING GIN (sha gin_trgm_ops);
CREATE INDEX ON commits USING GIN (author_login gin_trgm_ops);
CREATE INDEX ON commits USING GIN (agent_type gin_trgm_ops);
CREATE INDEX ON repos USING GIN (full_name gin_trgm_ops);
