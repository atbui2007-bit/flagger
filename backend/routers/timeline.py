from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, Query
from auth import CurrentUser, current_user
from database import get_db
from db.repos import get_repo

router = APIRouter()

async def get_timeline(limit, cursor, repo_id, session: AsyncSession):
    if cursor:
        lookup = text("SELECT pushed_at FROM commits WHERE id = :cursor_id")
        result = await session.execute(lookup, {"cursor_id": cursor})
        cursor_timestamp = result.scalar()
        where_clause = "WHERE commits.repo_id = :repo_id AND (commits.pushed_at, commits.id) < (:cursor_timestamp, :cursor_id)"
        params = {"limit": limit + 1, "cursor_timestamp": cursor_timestamp, "cursor_id": cursor, "repo_id": repo_id}
    else:
        where_clause = "WHERE commits.repo_id = :repo_id"
        params = {"limit": limit + 1, "repo_id": repo_id}

    query = text(f"""
        SELECT commits.*, repos.full_name, repos.owner
        FROM commits
        JOIN repos ON commits.repo_id = repos.id
        {where_clause}
        ORDER BY commits.pushed_at DESC
        LIMIT :limit
    """)

    result = await session.execute(query, params)
    rows = result.fetchall()
    has_more = len(rows) > limit
    if has_more:
        rows = rows[:-1]
    rows = [dict(row._mapping) for row in rows]
    next_cursor = rows[-1]["id"] if has_more else None
    return {
        "data": rows,
        "next_cursor": next_cursor,
        "has_more": has_more
    }

@router.get("/{owner}/{name}/timeline")
async def timeline(
    owner: str,
    name: str,
    limit: int = Query(default=20, le=100),
    cursor: str = Query(default=None),
    user: CurrentUser = Depends(current_user),
    session: AsyncSession = Depends(get_db)
):
    full_name = f"{owner}/{name}"
    repo = await get_repo(full_name, session, user=user)
    result = await get_timeline(limit, cursor, repo.id, session)
    return result
