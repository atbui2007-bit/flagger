from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends
from database import get_db
from db.repos import get_repo, get_pull_request_id

router = APIRouter()

async def get_pr_detail(pull_request_id, session: AsyncSession):
    pr_query = text("SELECT * FROM pull_requests WHERE id = :pull_request_id")
    pr_result = await session.execute(pr_query, {"pull_request_id": pull_request_id})
    pr_row = pr_result.fetchone()

    commits_query = text("""
        SELECT * FROM commits
        WHERE pull_request_id = :pull_request_id
        ORDER BY pushed_at DESC
    """)
    commits_result = await session.execute(commits_query, {"pull_request_id": pull_request_id})
    commits_rows = commits_result.fetchall()

    ci_runs_query = text("""
        SELECT * FROM ci_runs
        WHERE pull_request_id = :pull_request_id
        ORDER BY created_at DESC
    """)
    ci_runs_result = await session.execute(ci_runs_query, {"pull_request_id": pull_request_id})
    ci_runs_rows = ci_runs_result.fetchall()

    reviews_query = text("""
        SELECT * FROM reviews
        WHERE pull_request_id = :pull_request_id
        ORDER BY submitted_at DESC
    """)
    reviews_result = await session.execute(reviews_query, {"pull_request_id": pull_request_id})
    reviews_rows = reviews_result.fetchall()

    return {
        "pull_request": dict(pr_row._mapping),
        "commits": [dict(row._mapping) for row in commits_rows],
        "ci_runs": [dict(row._mapping) for row in ci_runs_rows],
        "reviews": [dict(row._mapping) for row in reviews_rows],
    }

@router.get("/{owner}/{name}/prs/{number}")
async def pr_detail(
    owner: str,
    name: str,
    number: int,
    session: AsyncSession = Depends(get_db)
):
    full_name = f"{owner}/{name}"
    repo_id = await get_repo(full_name, session)
    pull_request_id = await get_pull_request_id(number, repo_id, session)
    result = await get_pr_detail(pull_request_id, session)
    return result
