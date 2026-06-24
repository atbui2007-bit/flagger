from fastapi import HTTPException
from sqlalchemy import text

async def get_repo(full_name, session):
    query = text("SELECT id FROM repos WHERE full_name = :full_name")
    result = await session.execute(query, {"full_name": full_name})
    
    row = result.fetchone()
    if(not row):
       raise HTTPException(status_code = 404, detail = "not found")
    
    return row.id