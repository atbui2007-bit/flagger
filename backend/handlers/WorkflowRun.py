from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from db.repos import get_repo, get_pull_request_id
from datetime import datetime

def parse_dt(value):
    if value is None:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))

async def handle_workflow_run(payload, session: AsyncSession):
    repo_id = await get_repo(payload["repository"]["full_name"], session)
    pr_list = payload["workflow_run"]["pull_requests"]
    if not pr_list:
        return None
    
    pr_number  = pr_list[0]["number"]
    pull_request_id = await get_pull_request_id(pr_number, repo_id, session)
    run = payload["workflow_run"]

    upsert_query = text("""
    INSERT INTO ci_runs (
        id, pull_request_id, github_run_id, workflow_name,
        status, conclusion, started_at, completed_at, created_at
    )
    VALUES (
        gen_random_uuid(), :pull_request_id, :github_run_id, :workflow_name,
        :status, :conclusion, :started_at, :completed_at, :created_at
    )
    ON CONFLICT (github_run_id)
    DO UPDATE SET
        status = EXCLUDED.status,
        conclusion = EXCLUDED.conclusion,
        completed_at = EXCLUDED.completed_at
""")

    await session.execute(upsert_query, {
        "pull_request_id": pull_request_id,
        "github_run_id": run["id"],
        "workflow_name": run["name"],
        "status": run["status"],
        "conclusion": run.get("conclusion"),
        "started_at": parse_dt(run["run_started_at"]),
        "completed_at": parse_dt(run.get("updated_at")),
        "created_at": parse_dt(run["created_at"])
    })
    
    await session.commit()