from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from auth import CurrentUser, current_user
from database import get_db
import github_app
from github_client import github_request
from log_config import get_logger

logger = get_logger(__name__)
router = APIRouter()


class ClaimRequest(BaseModel):
    # GitHub installation id from the App Setup URL redirect (?installation_id=...)
    installation_id: int
    # GitHub OAuth access token from the Supabase session (session.provider_token)
    provider_token: str


class SyncAccessRequest(BaseModel):
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


async def _paginate_user_collection(path, key, provider_token):
    items = []
    page = 1
    while True:
        body = await _github_json(
            "GET", f"{path}?per_page=100&page={page}", provider_token
        )
        page_items = body.get(key, [])
        items.extend(page_items)
        if len(page_items) < 100:
            return items
        page += 1


async def _find_user_installation(installation_id, provider_token):
    # /user/installations lists installations the token's GitHub user can access.
    installations = await _paginate_user_collection(
        "/user/installations", "installations", provider_token
    )
    for installation in installations:
        if installation.get("id") == installation_id:
            return installation
    return None


def _highest_permission(permissions):
    for permission in ("admin", "maintain", "push", "triage", "pull"):
        if permissions.get(permission):
            return permission
    return None


def _claim_access_level(account_type, account_login, github_user_login, full_repos, user_repos):
    if account_type == "User":
        return "admin" if account_login == github_user_login else "member"

    full_repo_ids = {repo.get("id") for repo in full_repos}
    user_repos_by_id = {repo.get("id"): repo for repo in user_repos}
    # Empty coverage list (zero-repo installation or API hiccup) must never
    # read as "full coverage" — issubset of the empty set is vacuously true.
    if not full_repo_ids or not full_repo_ids.issubset(user_repos_by_id.keys()):
        return "member"
    for repo_id in full_repo_ids:
        permissions = user_repos_by_id[repo_id].get("permissions") or {}
        if not permissions.get("admin"):
            return "member"
    return "admin"


async def _paginate_installation_collection(path, key, installation_token):
    items = []
    page = 1
    while True:
        body = await _github_json(
            "GET", f"{path}?per_page=100&page={page}", installation_token
        )
        page_items = body.get(key, [])
        items.extend(page_items)
        if len(page_items) < 100:
            return items
        page += 1


async def _repo_member_grants_for_installation(session, installation_id):
    repos_result = await session.execute(text("""
        SELECT id, github_repo_id
        FROM repos
        WHERE installation_id = :installation_id
          AND github_repo_id IS NOT NULL
          AND removed_at IS NULL
    """), {"installation_id": installation_id})
    return {
        row.github_repo_id: row.id
        for row in repos_result.fetchall()
    }


async def _upsert_repo_member_grants(session, grants):
    if not grants:
        return
    upsert_repo_member = text("""
        INSERT INTO repo_members (
            repo_id, supabase_user_id, github_login, role,
            github_permission, access_checked_at, access_expires_at
        )
        VALUES (
            :repo_id, :supabase_user_id, :github_login, 'member',
            :github_permission, NOW(), NOW() + interval '24 hours'
        )
        ON CONFLICT (repo_id, supabase_user_id) DO UPDATE SET
            github_login = EXCLUDED.github_login,
            role = 'member',
            github_permission = EXCLUDED.github_permission,
            access_checked_at = NOW(),
            access_expires_at = NOW() + interval '24 hours',
            removed_at = NULL
    """)
    for grant in grants:
        await session.execute(upsert_repo_member, grant)


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

    account = installation["account"]
    full_repos = []
    user_repos = []
    if not (account["type"] == "User" and account["login"] == github_user["login"]):
        installation_token = await github_app.get_installation_token(installation["id"])
        full_repos = await _paginate_installation_collection(
            "/installation/repositories", "repositories", installation_token
        )
        user_repos = await _paginate_user_collection(
            f"/user/installations/{installation['id']}/repositories",
            "repositories",
            body.provider_token,
        )

    access_level = _claim_access_level(
        account["type"],
        account["login"],
        github_user["login"],
        full_repos,
        user_repos,
    )

    if access_level == "member":
        installation_result = await session.execute(text("""
            SELECT id
            FROM installations
            WHERE github_installation_id = :gid
              AND deleted_at IS NULL
        """), {"gid": installation["id"]})
        installation_row = installation_result.fetchone()
        if installation_row is None:
            raise HTTPException(status_code=409, detail="installation is not tracked")

        tracked_repos = await _repo_member_grants_for_installation(session, installation_row.id)
        grants = []
        for github_repo in user_repos:
            repo_id = tracked_repos.get(github_repo.get("id"))
            if repo_id is None:
                continue
            grants.append({
                "repo_id": repo_id,
                "supabase_user_id": user.id,
                "github_login": github_user["login"],
                "github_permission": _highest_permission(github_repo.get("permissions") or {}),
            })
        await _upsert_repo_member_grants(session, grants)
        await session.commit()
        logger.info("installation repo access claimed", extra={
            "github_installation_id": installation["id"],
            "account_login": account["login"],
            "repo_grants": len(grants),
        })
        return {
            "status": "member",
            "installation_id": installation["id"],
            "account_login": account["login"],
        }

    # Same idempotent upsert as handlers/Installation.py -- whichever of the
    # installation webhook or this claim lands first, the other converges.
    # A successful live admin claim proves the installation currently exists on
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
        "login": account["login"],
        "account_type": account["type"],
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
        "account_login": account["login"],
    })
    return {
        "status": "claimed",
        "installation_id": installation["id"],
        "account_login": account["login"],
    }


@router.post("/sync-access")
async def sync_access(
    body: SyncAccessRequest,
    user: CurrentUser = Depends(current_user),
    session: AsyncSession = Depends(get_db),
):
    if user.auth_disabled:
        raise HTTPException(status_code=400, detail="sync unavailable when auth is disabled")

    github_user = await _github_json("GET", "/user", body.provider_token)
    if user.github_id is None or str(github_user.get("id")) != str(user.github_id):
        raise HTTPException(status_code=403, detail="token does not match authenticated user")

    user_installations = await _paginate_user_collection(
        "/user/installations", "installations", body.provider_token
    )
    tracked_result = await session.execute(text("""
        SELECT id, github_installation_id
        FROM installations
        WHERE deleted_at IS NULL
    """))
    tracked = {
        row.github_installation_id: row.id
        for row in tracked_result.fetchall()
    }

    granted = 0
    removed = 0
    failed_installation_ids = []
    for installation in user_installations:
        github_installation_id = installation.get("id")
        installation_id = tracked.get(github_installation_id)
        if installation_id is None:
            continue

        tracked_repos = await _repo_member_grants_for_installation(session, installation_id)

        try:
            github_repos = await _paginate_user_collection(
                f"/user/installations/{github_installation_id}/repositories",
                "repositories",
                body.provider_token,
            )
        except HTTPException:
            failed_installation_ids.append(github_installation_id)
            continue

        grants = []
        for github_repo in github_repos:
            repo_id = tracked_repos.get(github_repo.get("id"))
            if repo_id is None:
                continue
            grants.append({
                "repo_id": repo_id,
                "supabase_user_id": user.id,
                "github_login": github_user["login"],
                "github_permission": _highest_permission(github_repo.get("permissions") or {}),
            })

        if grants:
            await _upsert_repo_member_grants(session, grants)
            granted += len(grants)

        removal_params = {
            "supabase_user_id": user.id,
            "installation_id": installation_id,
        }
        removal_sql = """
            UPDATE repo_members
            SET removed_at = NOW()
            WHERE supabase_user_id = :supabase_user_id
              AND removed_at IS NULL
              AND repo_id IN (
                  SELECT id FROM repos
                  WHERE installation_id = :installation_id
                    AND removed_at IS NULL
              )
        """
        if grants:
            placeholders = []
            for index, grant in enumerate(grants):
                key = f"granted_repo_id_{index}"
                placeholders.append(f":{key}")
                removal_params[key] = grant["repo_id"]
            removal_sql += f" AND repo_id NOT IN ({', '.join(placeholders)})"
        removal_result = await session.execute(text(removal_sql), removal_params)
        removed += removal_result.rowcount

    await session.commit()
    response = {"status": "ok", "granted": granted, "removed": removed}
    if failed_installation_ids:
        response["status"] = "partial"
        response["failed_installation_ids"] = failed_installation_ids
    return response


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
                   i.installed_at, i.suspended_at, i.deleted_at,
                   COALESCE(im.role, 'member') AS role,
                   CASE WHEN im.role = 'admin' THEN
                       (SELECT COUNT(*) FROM repos r
                         WHERE r.installation_id = i.id AND r.removed_at IS NULL)
                   ELSE
                       (SELECT COUNT(*) FROM repos r
                        JOIN repo_members rm ON rm.repo_id = r.id
                         WHERE r.installation_id = i.id
                           AND r.removed_at IS NULL
                           AND rm.supabase_user_id = :auth_user_id
                           AND rm.removed_at IS NULL
                           AND rm.access_expires_at > NOW())
                   END AS repo_count
            FROM installations i
            LEFT JOIN installation_members im
              ON im.installation_id = i.id
             AND im.supabase_user_id = :auth_user_id
             AND im.removed_at IS NULL
            WHERE im.id IS NOT NULL OR EXISTS (
                SELECT 1 FROM repos r
                JOIN repo_members rm ON rm.repo_id = r.id
                WHERE r.installation_id = i.id
                  AND r.removed_at IS NULL
                  AND rm.supabase_user_id = :auth_user_id
                  AND rm.removed_at IS NULL
                  AND rm.access_expires_at > NOW()
            )
            ORDER BY i.installed_at DESC
        """), {"auth_user_id": user.id})
    return {"data": [dict(row._mapping) for row in result.fetchall()]}
