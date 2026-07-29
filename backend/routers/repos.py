from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from auth import CurrentUser, current_user, repo_entitlement_filter
from database import get_db

router = APIRouter()


@router.get("")
async def repos(
    user: CurrentUser = Depends(current_user),
    session: AsyncSession = Depends(get_db),
):
    clauses, params = repo_entitlement_filter(user)
    clauses.append("repos.removed_at IS NULL")
    where_clause = f"WHERE {' AND '.join(clauses)}" if clauses else ""

    query = text(f"""
        SELECT repos.full_name, repos.owner, repos.name, repos.installed_at,
               installations.account_login
        FROM repos
        LEFT JOIN installations ON installations.id = repos.installation_id
        {where_clause}
        ORDER BY repos.full_name
    """)

    result = await session.execute(query, params)
    rows = result.fetchall()
    return {"data": [dict(row._mapping) for row in rows]}
