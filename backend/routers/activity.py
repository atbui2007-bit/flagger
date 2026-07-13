from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from auth import CurrentUser, current_user, entitlement_filter
from database import get_db

router = APIRouter()


def activity_filters(
    user: CurrentUser,
    repository: Optional[str],
    contributor: Optional[str],
    agent: Optional[str],
    risk: Optional[str],
    confidence: Optional[str],
    search: Optional[str],
):
    clauses, params = entitlement_filter(user)

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
        # Dashboard filters by tier (high/medium/low); the DB stores the raw
        # claim (certain/likely/suspected). Literals are fixed constants here,
        # never user input.
        tier = {
            "high": "('certain', 'high')",
            "medium": "('likely', 'medium')",
            "low": "('suspected', 'low')",
        }.get(confidence.lower())
        if tier:
            clauses.append(f"LOWER(commits.attribution_confidence) IN {tier}")
        else:
            clauses.append("LOWER(commits.attribution_confidence) = :confidence")
            params["confidence"] = confidence.lower()
    if search:
        clauses.append("""(
            commits.message ILIKE :search OR
            commits.sha ILIKE :search OR
            commits.author_login ILIKE :search OR
            commits.agent_type ILIKE :search OR
            repos.full_name ILIKE :search
        )""")
        params["search"] = f"%{search.strip()}%"

    return clauses, params


async def get_activity_recent(
    user: CurrentUser,
    limit: int,
    cursor: Optional[str],
    repository: Optional[str],
    contributor: Optional[str],
    agent: Optional[str],
    risk: Optional[str],
    confidence: Optional[str],
    search: Optional[str],
    session: AsyncSession,
):
    clauses, params = activity_filters(user, repository, contributor, agent, risk, confidence, search)

    if cursor:
        try:
            UUID(cursor)
        except ValueError:
            # Malformed cursor: ignore it (first page), same as unknown ids below.
            cursor = None
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
        SELECT commits.*, repos.full_name, repos.owner, pull_requests.github_pr_number AS pr_number
        FROM commits
        JOIN repos ON commits.repo_id = repos.id
        LEFT JOIN pull_requests ON commits.pull_request_id = pull_requests.id
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
    search: Optional[str] = Query(default=None, max_length=200),
    user: CurrentUser = Depends(current_user),
    session: AsyncSession = Depends(get_db),
):
    return await get_activity_recent(
        user, limit, cursor, repository, contributor, agent, risk, confidence, search, session
    )


@router.get("/summary")
async def summary(
    repository: Optional[str] = Query(default=None),
    contributor: Optional[str] = Query(default=None),
    agent: Optional[str] = Query(default=None),
    risk: Optional[str] = Query(default=None),
    confidence: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None, max_length=200),
    user: CurrentUser = Depends(current_user),
    session: AsyncSession = Depends(get_db),
):
    clauses, params = activity_filters(user, repository, contributor, agent, risk, confidence, search)
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
async def facets(
    user: CurrentUser = Depends(current_user),
    session: AsyncSession = Depends(get_db),
):
    clauses, params = entitlement_filter(user)
    where_clause = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    query = text(f"""
        SELECT
            ARRAY_AGG(DISTINCT repos.full_name ORDER BY repos.full_name) AS repositories,
            ARRAY_AGG(DISTINCT commits.author_login ORDER BY commits.author_login) AS contributors,
            ARRAY_AGG(DISTINCT commits.agent_type ORDER BY commits.agent_type) AS agents
        FROM commits
        JOIN repos ON commits.repo_id = repos.id
        {where_clause}
    """)
    row = (await session.execute(query, params)).one()._mapping
    return {
        "repositories": row["repositories"] or [],
        "contributors": row["contributors"] or [],
        "agents": row["agents"] or [],
    }


@router.get("/agents")
async def agents(
    user: CurrentUser = Depends(current_user),
    session: AsyncSession = Depends(get_db),
):
    clauses, params = entitlement_filter(user)
    where_clause = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    query = text(f"""
        SELECT
            commits.agent_type,
            COUNT(*) AS commit_count,
            COUNT(DISTINCT commits.repo_id) AS repositories,
            COUNT(DISTINCT commits.author_login) AS contributors,
            COUNT(*) FILTER (WHERE commits.risk_no_review = TRUE) AS review_needed,
            COUNT(*) FILTER (
                WHERE LOWER(commits.attribution_confidence) IN ('certain', 'high')
            ) AS certain_attribution,
            COALESCE(SUM(commits.additions), 0) AS additions,
            COALESCE(SUM(commits.deletions), 0) AS deletions,
            MAX(commits.pushed_at) AS last_active,
            ARRAY_AGG(DISTINCT commits.attribution_source ORDER BY commits.attribution_source) AS sources
        FROM commits
        {where_clause}
        GROUP BY commits.agent_type
        ORDER BY commit_count DESC, commits.agent_type
    """)
    result = await session.execute(query, params)
    data = [dict(row._mapping) for row in result.fetchall()]
    for row in data:
        row["commits"] = row.pop("commit_count")
    return {"data": data}
