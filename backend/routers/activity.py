from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, Query
from database import get_db

router = APIRouter()

async def get_activity_recent(limit, cursor, session: AsyncSession):  
    if cursor:
        lookup = text("SELECT pushed_at FROM commits WHERE id = :cursor_id")
        result = await session.execute(lookup, {"cursor_id": cursor})
        cursor_timestamp = result.scalar()
        where_clause = "WHERE (commits.pushed_at, commits.id) < (:cursor_timestamp, :cursor_id)"
        params = {"limit": limit + 1, "cursor_timestamp": cursor_timestamp, "cursor_id": cursor}
    else:
        where_clause = ""
        params = {"limit": limit + 1}

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
    next_cursor = rows[-1].id if has_more else None
    return {
        "data": rows,
        "next_cursor": next_cursor,
        "has_more": has_more 
        }

@router.get("/recent")
async def recent(
    limit: int = Query(default=20, le=100),
    cursor: str = Query(default=None),
    session: AsyncSession = Depends(get_db)
):
    result = await get_activity_recent(limit, cursor, session)
    return result
