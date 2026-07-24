-- NOT YET APPLIED. Joint schema decision, sync with DB co-owner before applying.
-- F3 fix: /installations/claim and /sync-access now bind the provider token to the
-- GitHub id GoTrue recorded at OAuth (auth.identities), not the user-editable
-- user_metadata.provider_id. The backend role needs read access to that table.
-- ORDERING: apply this BEFORE deploying the matching backend code -- _trusted_github_id
-- selects from auth.identities and will error if the grant is missing.
--
-- Role is `postgres`: the DATABASE_URL pooler login `postgres.<project_ref>` is an
-- alias that authenticates AS the `postgres` database role. Confirm against your own
-- DATABASE_URL if the role prefix ever changes.
-- FIRST check whether the grant is even needed -- the Supabase `postgres` role often
-- already reads the auth schema. Connect as the backend and run:
--   SELECT identity_data FROM auth.identities WHERE provider = 'github' LIMIT 1;
-- If that returns rows (no "permission denied"), _trusted_github_id already works and
-- these GRANTs are a no-op you can skip. NOTE: on this project the GitHub id lives under
-- identity_data->>'sub' (->>'provider_id' is NULL); the helper COALESCEs both.

GRANT USAGE ON SCHEMA auth TO postgres;
GRANT SELECT ON auth.identities TO postgres;
