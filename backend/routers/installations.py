from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from auth import CurrentUser, current_user
from database import get_db
from github_client import github_request
from log_config import get_logger

logger = get_logger(__name__)
router = APIRouter()


class ClaimRequest(BaseModel):
    # GitHub installation id from the App Setup URL redirect (?installation_id=...)
    installation_id: int
    # GitHub OAuth access token from the Supabase session (session.provider_token)
    provider_token: str


async def _github_json(method, path, token):
    response = await github_request(method, path, token=token)
    if response.status_code == 401:
        raise HTTPException(status_code=403, detail="GitHub token expired or revoked")
    if response.status_code >= 500:
        raise HTTPException(status_code=502, detail="GitHub is unavailable")
    if response.status_code != 200:
        logger.warning("unexpected GitHub response", extra={"path": path, "status": response.status_code})
        raise HTTPException(status_code=502, detail="unexpected GitHub response")
    return response.json()


async def _find_user_installation(installation_id, provider_token):
    # /user/installations lists installations the token's GitHub user can access.
    for page in range(1, 11):
        body = await _github_json(
            "GET", f"/user/installations?per_page=100&page={page}", provider_token
        )
        items = body.get("installations", [])
        for item in items:
            if item.get("id") == installation_id:
                return item
        if len(items) < 100:
            break
    return None


@router.post("/claim")
async def claim(
    body: ClaimRequest,
    user: CurrentUser = Depends(current_user),
    session: AsyncSession = Depends(get_db),
):
    if user.auth_disabled:
        raise HTTPException(status_code=400, detail="claim unavailable when auth is disabled")

    # Bind the provider token to the signed-in user's GitHub identity so a
    # borrowed token for a different GitHub account can't claim installations.
    github_user = await _github_json("GET", "/user", body.provider_token)
    if user.github_id is None or str(github_user.get("id")) != str(user.github_id):
        raise HTTPException(status_code=403, detail="token does not match authenticated user")

    installation = await _find_user_installation(body.installation_id, body.provider_token)
    if installation is None:
        raise HTTPException(status_code=403, detail="installation not accessible to this GitHub user")

    # Same idempotent upsert as handlers/Installation.py -- whichever of the
    # installation webhook or this claim lands first, the other converges.
    # A successful live claim proves the installation currently exists on
    # GitHub, so resurrecting a stale soft-delete is correct.
    await session.execute(text("""
        INSERT INTO installations (github_installation_id, account_login, account_type)
        VALUES (:gid, :login, :account_type)
        ON CONFLICT (github_installation_id) DO UPDATE SET
            account_login = EXCLUDED.account_login,
            account_type = EXCLUDED.account_type,
            suspended_at = NULL,
            deleted_at = NULL
    """), {
        "gid": installation["id"],
        "login": installation["account"]["login"],
        "account_type": installation["account"]["type"],
    })

    await session.execute(text("""
        INSERT INTO installation_members (installation_id, supabase_user_id, github_login, role)
        VALUES ((SELECT id FROM installations WHERE github_installation_id = :gid),
                :supabase_user_id, :github_login, 'admin')
        ON CONFLICT (installation_id, supabase_user_id) DO UPDATE SET
            github_login = EXCLUDED.github_login,
            removed_at = NULL
    """), {
        "gid": installation["id"],
        "supabase_user_id": user.id,
        "github_login": github_user["login"],
    })
    await session.commit()
    logger.info("installation claimed", extra={
        "github_installation_id": installation["id"],
        "account_login": installation["account"]["login"],
    })
    return {
        "status": "claimed",
        "installation_id": installation["id"],
        "account_login": installation["account"]["login"],
    }


@router.get("")
async def list_installations(
    user: CurrentUser = Depends(current_user),
    session: AsyncSession = Depends(get_db),
):
    if user.auth_disabled:
        result = await session.execute(text("""
            SELECT i.github_installation_id, i.account_login, i.account_type,
                   i.installed_at, i.suspended_at, i.deleted_at,
                   (SELECT COUNT(*) FROM repos r
                     WHERE r.installation_id = i.id AND r.removed_at IS NULL) AS repo_count
            FROM installations i
            WHERE i.deleted_at IS NULL
            ORDER BY i.installed_at DESC
        """))
    else:
        result = await session.execute(text("""
            SELECT i.github_installation_id, i.account_login, i.account_type,
                   i.installed_at, i.suspended_at, i.deleted_at, im.role,
                   (SELECT COUNT(*) FROM repos r
                     WHERE r.installation_id = i.id AND r.removed_at IS NULL) AS repo_count
            FROM installation_members im
            JOIN installations i ON im.installation_id = i.id
            WHERE im.supabase_user_id = :auth_user_id AND im.removed_at IS NULL
            ORDER BY i.installed_at DESC
        """), {"auth_user_id": user.id})
    return {"data": [dict(row._mapping) for row in result.fetchall()]}
