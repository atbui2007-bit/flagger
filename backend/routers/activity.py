from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db

router = APIRouter()


def activity_filters(
    repository: Optional[str],
    contributor: Optional[str],
    agent: Optional[str],
    risk: Optional[str],
    confidence: Optional[str],
):
    clauses = []
    params = {}

    if repository:
        clauses.append("repos.full_name = :repository")
        params["repository"] = repository
    if contributor:
        clauses.append("commits.author_login = :contributor")
        params["contributor"] = contributor
    if agent:
        clauses.append("LOWER(commits.agent_type) LIKE :agent")
        params["agent"] = f"%{agent.lower()}%"
    if risk:
        clauses.append("commits.risk_level = :risk")
        params["risk"] = risk
    if confidence:
        clauses.append("LOWER(commits.attribution_confidence) = :confidence")
        params["confidence"] = confidence.lower()

    return clauses, params


async def get_activity_recent(
    limit: int,
    cursor: Optional[str],
    repository: Optional[str],
    contributor: Optional[str],
    agent: Optional[str],
    risk: Optional[str],
    confidence: Optional[str],
    session: AsyncSession,
):
    clauses, params = activity_filters(repository, contributor, agent, risk, confidence)

    if cursor:
        lookup = text("SELECT pushed_at FROM commits WHERE id = :cursor_id")
        result = await session.execute(lookup, {"cursor_id": cursor})
        cursor_timestamp = result.scalar()
        if cursor_timestamp is not None:
            clauses.append("(commits.pushed_at, commits.id) < (:cursor_timestamp, :cursor_id)")
            params.update({"cursor_timestamp": cursor_timestamp, "cursor_id": cursor})

    where_clause = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    params["limit"] = limit + 1

    query = text(f"""
        SELECT commits.*, repos.full_name, repos.owner
        FROM commits
        JOIN repos ON commits.repo_id = repos.id
        {where_clause}
        ORDER BY commits.pushed_at DESC, commits.id DESC
        LIMIT :limit
    """)

    result = await session.execute(query, params)
    rows = result.fetchall()
    has_more = len(rows) > limit
    if has_more:
        rows = rows[:-1]
    data = [dict(row._mapping) for row in rows]
    return {
        "data": data,
        "next_cursor": data[-1]["id"] if has_more and data else None,
        "has_more": has_more,
    }


@router.get("/recent")
async def recent(
    limit: int = Query(default=20, ge=1, le=100),
    cursor: Optional[str] = Query(default=None),
    repository: Optional[str] = Query(default=None),
    contributor: Optional[str] = Query(default=None),
    agent: Optional[str] = Query(default=None),
    risk: Optional[str] = Query(default=None),
    confidence: Optional[str] = Query(default=None),
    session: AsyncSession = Depends(get_db),
):
    return await get_activity_recent(
        limit, cursor, repository, contributor, agent, risk, confidence, session
    )


@router.get("/summary")
async def summary(
    repository: Optional[str] = Query(default=None),
    contributor: Optional[str] = Query(default=None),
    agent: Optional[str] = Query(default=None),
    risk: Optional[str] = Query(default=None),
    confidence: Optional[str] = Query(default=None),
    session: AsyncSession = Depends(get_db),
):
    clauses, params = activity_filters(repository, contributor, agent, risk, confidence)
    where_clause = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    query = text(f"""
        SELECT
            COUNT(*) AS total_commits,
            COUNT(*) FILTER (WHERE LOWER(commits.agent_type) NOT IN ('human', 'unknown')) AS ai_authored_commits,
            COUNT(DISTINCT commits.repo_id) AS repositories,
            COUNT(*) FILTER (WHERE commits.risk_no_review = TRUE) AS review_needed
        FROM commits
        JOIN repos ON commits.repo_id = repos.id
        {where_clause}
    """)
    result = await session.execute(query, params)
    row = result.one()._mapping
    total = row["total_commits"] or 0
    ai_authored = row["ai_authored_commits"] or 0
    return {
        "total_commits": total,
        "ai_authored_commits": ai_authored,
        "ai_share_percent": round((ai_authored / total) * 100, 1) if total else 0,
        "repositories": row["repositories"] or 0,
        "review_needed": row["review_needed"] or 0,
    }


@router.get("/facets")
async def facets(session: AsyncSession = Depends(get_db)):
    query = text("""
        SELECT
            ARRAY_AGG(DISTINCT repos.full_name ORDER BY repos.full_name) AS repositories,
            ARRAY_AGG(DISTINCT commits.author_login ORDER BY commits.author_login) AS contributors,
            ARRAY_AGG(DISTINCT commits.agent_type ORDER BY commits.agent_type) AS agents
        FROM commits
        JOIN repos ON commits.repo_id = repos.id
    """)
    row = (await session.execute(query)).one()._mapping
    return {
        "repositories": row["repositories"] or [],
        "contributors": row["contributors"] or [],
        "agents": row["agents"] or [],
    }
