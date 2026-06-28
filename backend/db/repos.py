from fastapi import HTTPException
from sqlalchemy import text

async def get_repo(full_name, session):
    query = text("SELECT id FROM repos WHERE full_name = :full_name")
    result = await session.execute(query, {"full_name": full_name})
    
    row = result.fetchone()
    if(not row):
       raise HTTPException(status_code = 404, detail = "not found")
    
    return row.id

async def get_pull_request_id(github_pr_number, repo_id, session):
   query = text(SELECT id FROM pull_requests WHERE github_pr_number = :github_pr_number AND repo_id = :repo_id)
   result = await session.execute(query, {"github_pr_number": github_pr_number, "repo_id": repo_id})

   row = result.fetchone()
   if not row:
      raise HTTPException(status_code = 404, detail = "not found")
   
   return row.id