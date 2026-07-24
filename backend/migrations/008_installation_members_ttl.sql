-- NOT YET APPLIED. Joint schema decision, sync with DB co-owner before applying. Apply 007 first.
-- Gives installation-wide grants the same TTL model repo_members already uses (migration 006):
-- an off-boarded org admin should lose read access once their membership stops revalidating via
-- sync-access, not keep it until someone manually sets removed_at.
-- ORDERING: apply this BEFORE deploying the matching backend code -- the entitlement predicates
-- reference im.access_expires_at, and a missing column errors regardless of NULL-tolerance (the
-- NULL guard only covers rows inserted before the backfill runs, not an absent column).

ALTER TABLE installation_members ADD COLUMN access_expires_at timestamptz;

-- Existing rows get a 24h grace window so nobody is instantly locked out on deploy; the next
-- sync-access refreshes still-valid memberships and lets truly stale ones expire.
UPDATE installation_members
SET access_expires_at = NOW() + interval '24 hours'
WHERE access_expires_at IS NULL AND removed_at IS NULL;
