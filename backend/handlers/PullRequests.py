from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from db.repos import get_repo
from datetime import datetime, timezone

def parse_dt(value):
    if value is None:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))

async def handle_pull_request(payload, session: AsyncSession):
    repo_id = await get_repo(payload["repository"]["full_name"], session)
    
    pr = payload["pull_request"]
    
    upsert_query = text("""
        INSERT INTO pull_requests (
            id, repo_id, github_pr_number, title, url,
            author_login, state, merged_at, created_at,
            updated_at, closed_at
        )
        VALUES (
            gen_random_uuid(), :repo_id, :github_pr_number, :title, :url, :author_login, :state, :merged_at, :created_at, :updated_at, :closed_at
        )
        ON CONFLICT (github_pr_number, repo_id)
        DO UPDATE SET
            state = EXCLUDED.state,
            updated_at = EXCLUDED.updated_at,
            merged_at = EXCLUDED.merged_at,
            closed_at = EXCLUDED.closed_at
    """)
    
    await session.execute(upsert_query, {
        "repo_id": repo_id,
        "github_pr_number": pr["number"],
        "title": pr["title"],
        "url": pr["html_url"],
        "author_login": pr["user"]["login"],
        "state": pr["state"],
        "merged_at": parse_dt(pr.get("merged_at")),
        "created_at": parse_dt(pr["created_at"]),
        "updated_at": parse_dt(pr["updated_at"]),
        "closed_at": parse_dt(pr.get("closed_at"))
    })
    
    await session.commit()