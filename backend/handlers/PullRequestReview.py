from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from db.repos import get_repo, get_pull_request_id
from datetime import datetime
from risk_recompute import recompute_for_pull_request

def parse_dt(value):
    if value is None:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))

async def handle_pull_request_review(payload, session: AsyncSession):
    repo = await get_repo(payload["repository"]["full_name"], session)
    repo_id = repo.id
    
    pr_number = payload["pull_request"]["number"]
    pull_request_id = await get_pull_request_id(pr_number, repo_id, session)
    review = payload["review"]

    upsert_query = text("""
    INSERT INTO reviews (
        id, pull_request_id, github_review_id, reviewer_login, 
        state, submitted_at, created_at
    )
    VALUES (
        gen_random_uuid(), :pull_request_id, :github_review_id, :reviewer_login,
        :state, :submitted_at, :created_at
    )
    ON CONFLICT (github_review_id)
    DO UPDATE SET
        state = EXCLUDED.state
""")

    await session.execute(upsert_query, {
        "pull_request_id": pull_request_id,
        "github_review_id": review["id"],
        "reviewer_login": review["user"]["login"],
        "state": review["state"],
        "submitted_at": parse_dt(review["submitted_at"]),
        # Review webhook objects carry submitted_at but no created_at.
        "created_at": parse_dt(review.get("created_at") or review["submitted_at"])
    })
    await recompute_for_pull_request(pull_request_id, session)
    await session.commit()
