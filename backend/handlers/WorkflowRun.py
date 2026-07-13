from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from db.repos import get_repo, get_pull_request_id
from datetime import datetime
from github_app import repo_token
from github_client import github_request
from handlers.PullRequests import upsert_pull_request
from log_config import get_logger
from risk_recompute import recompute_for_pull_request

logger = get_logger(__name__)

def parse_dt(value):
    if value is None:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))

async def handle_workflow_run(payload, session: AsyncSession):
    repo = await get_repo(payload["repository"]["full_name"], session)
    repo_id = repo.id
    pr_list = payload["workflow_run"]["pull_requests"]
    if not pr_list:
        logger.info("skipping workflow_run without pull_requests", extra={"repo": repo.full_name})
        return None
    
    pr_number  = pr_list[0]["number"]
    pull_request_id = await get_pull_request_id(pr_number, repo_id, session, required=False)
    if pull_request_id is None:
        token = await repo_token(repo)
        response = await github_request("GET", f"/repos/{repo.full_name}/pulls/{pr_number}", token=token)
        if response.status_code != 200:
            logger.warning(
                "skipping workflow_run because pull request fetch failed",
                extra={"repo": repo.full_name, "pr_number": pr_number, "status": response.status_code},
            )
            return None
        pull_request_id = await upsert_pull_request(response.json(), repo_id, session)
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
    await recompute_for_pull_request(pull_request_id, session)
    await session.commit()
