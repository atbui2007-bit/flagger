from fastapi import HTTPException
from sqlalchemy import text
from typing import NamedTuple


class RepoInfo(NamedTuple):
    id: object
    installation_id: object
    default_branch: str
    attribution_mode: str
    full_name: str
    github_installation_id: int | None
    installation_suspended_at: object
    installation_deleted_at: object

async def get_repo(full_name, session, user=None):
    # user=None is the webhook/handler path (no entitlement check). When a
    # CurrentUser is passed, unentitled repos 404 exactly like missing ones --
    # a 403 would confirm the repo is tracked, which is an existence leak.
    sql = """SELECT r.id, r.installation_id, r.default_branch, r.attribution_mode,
                    r.full_name, i.github_installation_id,
                    i.suspended_at, i.deleted_at
             FROM repos r
             LEFT JOIN installations i ON r.installation_id = i.id
             WHERE r.full_name = :full_name AND r.removed_at IS NULL"""
    params = {"full_name": full_name}
    if user is not None and not user.auth_disabled:
        sql += """ AND (
                EXISTS (
                    SELECT 1 FROM installation_members im
                    WHERE im.installation_id = r.installation_id
                      AND im.supabase_user_id = :auth_user_id
                      AND im.removed_at IS NULL
                      AND (im.access_expires_at IS NULL OR im.access_expires_at > NOW())
                )
                OR EXISTS (
                    SELECT 1 FROM repo_members rm
                    WHERE rm.repo_id = r.id
                      AND rm.supabase_user_id = :auth_user_id
                      AND rm.removed_at IS NULL
                      AND rm.access_expires_at > NOW()
                )
            )"""
        params["auth_user_id"] = user.id
    result = await session.execute(text(sql), params)
    
    row = result.fetchone()
    if(not row):
       raise HTTPException(status_code = 404, detail = "not found")
    
    return RepoInfo(*row)

async def get_pull_request_id(github_pr_number, repo_id, session, required: bool = True):
   query = text("""SELECT id FROM pull_requests WHERE github_pr_number = :github_pr_number AND repo_id = :repo_id""")
   result = await session.execute(query, {"github_pr_number": github_pr_number, "repo_id": repo_id})

   row = result.fetchone()
   if not row:
      if not required:
         return None
      raise HTTPException(status_code = 404, detail = "not found")
   
   return row.id
