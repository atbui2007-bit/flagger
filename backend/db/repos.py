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

async def get_repo(full_name, session):
    query = text("""SELECT r.id, r.installation_id, r.default_branch, r.attribution_mode,
                           r.full_name, i.github_installation_id,
                           i.suspended_at, i.deleted_at
                    FROM repos r
                    LEFT JOIN installations i ON r.installation_id = i.id
                    WHERE r.full_name = :full_name AND r.removed_at IS NULL""")
    result = await session.execute(query, {"full_name": full_name})
    
    row = result.fetchone()
    if(not row):
       raise HTTPException(status_code = 404, detail = "not found")
    
    return RepoInfo(*row)

async def get_pull_request_id(github_pr_number, repo_id, session):
   query = text("""SELECT id FROM pull_requests WHERE github_pr_number = :github_pr_number AND repo_id = :repo_id""")
   result = await session.execute(query, {"github_pr_number": github_pr_number, "repo_id": repo_id})

   row = result.fetchone()
   if not row:
      raise HTTPException(status_code = 404, detail = "not found")
   
   return row.id
