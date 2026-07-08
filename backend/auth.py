import os

import jwt
from fastapi import Header, HTTPException

from log_config import get_logger

logger = get_logger(__name__)
AUTH_DISABLED = os.getenv("AUTH_DISABLED", "").lower() == "true"
if AUTH_DISABLED:
    logger.warning("authentication is disabled")

_jwks_client = jwt.PyJWKClient(
    "https://www.googleapis.com/service_accounts/v1/jwk/securetoken@system.gserviceaccount.com"
)


async def require_user(authorization: str | None = Header(default=None)):
    if AUTH_DISABLED:
        return {"auth_disabled": True}
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing bearer token")
    project_id = os.getenv("FIREBASE_PROJECT_ID")
    if not project_id:
        raise HTTPException(status_code=401, detail="authentication is not configured")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        signing_key = _jwks_client.get_signing_key_from_jwt(token)
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=project_id,
            issuer=f"https://securetoken.google.com/{project_id}",
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(status_code=401, detail="invalid bearer token") from exc
