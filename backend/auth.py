import os
from dataclasses import dataclass

import jwt
from fastapi import Depends, Header, HTTPException

from log_config import get_logger

logger = get_logger(__name__)
AUTH_DISABLED = os.getenv("AUTH_DISABLED", "").lower() == "true"
if AUTH_DISABLED and os.getenv("RAILWAY_ENVIRONMENT"):
    raise RuntimeError("AUTH_DISABLED must not be set in production")
if AUTH_DISABLED:
    logger.warning("authentication is disabled")

# Lazily constructed: SUPABASE_URL is read at request time, matching the
# previous behavior of failing with a 401 (not an import error) when unset.
_jwks_client: jwt.PyJWKClient | None = None


def _get_jwks_client(supabase_url: str) -> jwt.PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        _jwks_client = jwt.PyJWKClient(
            f"{supabase_url}/auth/v1/.well-known/jwks.json"
        )
    return _jwks_client


async def require_user(authorization: str | None = Header(default=None)):
    if AUTH_DISABLED:
        return {"auth_disabled": True}
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing bearer token")
    supabase_url = os.getenv("SUPABASE_URL", "").rstrip("/")
    if not supabase_url:
        raise HTTPException(status_code=401, detail="authentication is not configured")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        # Legacy Supabase projects sign with a shared HS256 secret; projects on
        # the newer asymmetric signing keys are verified via the JWKS endpoint.
        jwt_secret = os.getenv("SUPABASE_JWT_SECRET")
        if jwt_secret:
            key = jwt_secret
            algorithms = ["HS256"]
        else:
            key = _get_jwks_client(supabase_url).get_signing_key_from_jwt(token).key
            algorithms = ["ES256", "RS256"]
        return jwt.decode(
            token,
            key,
            algorithms=algorithms,
            audience="authenticated",
            issuer=f"{supabase_url}/auth/v1",
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="invalid bearer token") from exc


@dataclass(frozen=True)
class CurrentUser:
    id: str | None            # Supabase JWT sub
    github_login: str | None  # user_metadata.user_name (GitHub OAuth provider)
    github_id: str | None     # user_metadata.provider_id (GitHub numeric user id)
    auth_disabled: bool = False


async def current_user(claims: dict = Depends(require_user)) -> CurrentUser:
    if claims.get("auth_disabled"):
        return CurrentUser(id=None, github_login=None, github_id=None, auth_disabled=True)
    meta = claims.get("user_metadata") or {}
    return CurrentUser(
        id=claims["sub"],
        github_login=meta.get("user_name"),
        github_id=meta.get("provider_id") or meta.get("sub"),
    )


# Entitlement: a user sees commits through either an active installation-wide
# membership or a live repo-scoped membership. Kept as an IN-subquery so it
# composes with the existing clauses/params pattern in one round-trip.
ENTITLED_COMMITS_PREDICATE = """commits.repo_id IN (
    SELECT r.id FROM repos r
    JOIN installation_members im ON im.installation_id = r.installation_id
    WHERE im.supabase_user_id = :auth_user_id AND im.removed_at IS NULL
      AND (im.access_expires_at IS NULL OR im.access_expires_at > NOW())
    UNION
    SELECT rm.repo_id FROM repo_members rm
    WHERE rm.supabase_user_id = :auth_user_id
      AND rm.removed_at IS NULL
      AND rm.access_expires_at > NOW()
)"""


def entitlement_filter(user: CurrentUser) -> tuple[list[str], dict]:
    if user.auth_disabled:
        return [], {}
    return [ENTITLED_COMMITS_PREDICATE], {"auth_user_id": user.id}
