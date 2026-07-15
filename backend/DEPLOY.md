# Deploying the backend to Railway

## Create the service

1. Create a Railway service from this GitHub repository.
2. Set the service Root Directory to `backend`. Railway will use `railway.json` and
   the existing Dockerfile from that directory.
3. Deploy. The Dockerfile starts uvicorn using Railway's injected `PORT` value.

## Configure environment variables

Set these service variables in Railway; do not commit secrets:

- `DATABASE_URL`: the `postgresql+asyncpg://` URL through the Supabase pooler on port
  `6543`.
- `WEBHOOK_SECRET`: the secret configured on the GitHub App webhook.
- `GITHUB_APP_ID`: the GitHub App ID.
- `GITHUB_APP_PRIVATE_KEY`: the private key as a `\n`-escaped PEM (literal backslash-n
  in place of newlines). Use this inline
  value on Railway, not `GITHUB_APP_PRIVATE_KEY_PATH`.
- `SUPABASE_URL`: the Supabase project URL.
- `CORS_ALLOWED_ORIGINS`: the dashboard origin.
- `SENTRY_DSN`: optional error-reporting DSN.

Never set `AUTH_DISABLED` in a deployed environment. Leave `SQL_ECHO` unset (or set
it to `false`) unless temporarily debugging SQL in a safe environment.

## GitHub App and database checklist

1. Set the GitHub App webhook URL to `https://<railway-domain>/webhook` and configure
   the matching webhook secret.
2. Enable the Supabase GitHub OAuth provider.
3. Apply migrations `002` through `005` with the database collaborator; this is a
   joint decision under §11.9 of `CLAUDE.md`.
4. Verify `user_metadata.provider_id` against a real Supabase GitHub-OAuth session.

## Healthcheck and verification

Railway checks `GET /health` as configured in `railway.json`. After deployment, confirm
`https://<railway-domain>/health` returns `{"status":"ok"}` and exercise the GitHub
App webhook flow.

## Rollback

If a deployment fails, roll back to the previous successful Railway deployment. Keep
database migrations coordinated with the database collaborator; do not roll back a
schema change independently of the application and database plan.
