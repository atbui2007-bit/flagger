from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from db.repos import get_repo
from risk_recompute import recompute_for_pull_request
from datetime import datetime, timezone

def parse_dt(value):
    if value is None:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))

async def handle_pull_request(payload, session: AsyncSession):
    repo = await get_repo(payload["repository"]["full_name"], session)
    repo_id = repo.id
    pr = payload["pull_request"]
    head_branch = pr["head"]["ref"]

    pull_request_id = await upsert_pull_request(pr, repo_id, session)

    # Backfill: link any commits pushed to this branch before the PR existed
    if payload["action"] == "opened" or payload["action"] == "reopened":
        backfill_query = text("""
            UPDATE commits SET pull_request_id = :pull_request_id
            WHERE repo_id = :repo_id AND branch = :head_branch AND pull_request_id IS NULL
        """)
        await session.execute(backfill_query, {
            "pull_request_id": pull_request_id,
            "repo_id": repo_id,
            "head_branch": head_branch,
        })

    await session.commit()

async def upsert_pull_request(pr, repo_id, session: AsyncSession):
    head_branch = pr["head"]["ref"]

    upsert_query = text("""
        INSERT INTO pull_requests (
            id, repo_id, github_pr_number, title, url,
            author_login, state, head_branch, merged_at, created_at,
            updated_at, closed_at
        )
        VALUES (
            gen_random_uuid(), :repo_id, :github_pr_number, :title, :url, :author_login, :state, :head_branch, :merged_at, :created_at, :updated_at, :closed_at
        )
        ON CONFLICT (github_pr_number, repo_id)
        DO UPDATE SET
            title = EXCLUDED.title,
            url = EXCLUDED.url,
            author_login = EXCLUDED.author_login,
            state = EXCLUDED.state,
            head_branch = EXCLUDED.head_branch,
            updated_at = EXCLUDED.updated_at,
            merged_at = EXCLUDED.merged_at,
            closed_at = EXCLUDED.closed_at
        RETURNING id
    """)
    
    result = await session.execute(upsert_query, {
        "repo_id": repo_id,
        "github_pr_number": pr["number"],
        "title": pr["title"],
        "url": pr["html_url"],
        "author_login": pr["user"]["login"],
        "state": pr["state"],
        "head_branch": head_branch,
        "merged_at": parse_dt(pr.get("merged_at")),
        "created_at": parse_dt(pr["created_at"]),
        "updated_at": parse_dt(pr["updated_at"]),
        "closed_at": parse_dt(pr.get("closed_at"))
    })
    pull_request_id = result.scalar()

    # Backfill: link any commits pushed to this branch before the PR existed
    if payload["action"] == "opened" or payload["action"] == "reopened":
        backfill_query = text("""
            UPDATE commits SET pull_request_id = :pull_request_id
            WHERE repo_id = :repo_id AND branch = :head_branch AND pull_request_id IS NULL
        """)
        await session.execute(backfill_query, {
            "pull_request_id": pull_request_id,
            "repo_id": repo_id,
            "head_branch": head_branch,
        })
        # Backfilled commits carry push-time risk flags from before the PR
        # existed; re-score them now rather than waiting on a review/CI event.
        await recompute_for_pull_request(pull_request_id, session)

    await session.commit()
