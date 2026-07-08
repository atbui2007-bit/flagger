import os

import jwt
from fastapi import Header, HTTPException

from log_config import get_logger

logger = get_logger(__name__)
AUTH_DISABLED = os.getenv("AUTH_DISABLED", "").lower() == "true"
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
