from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()
databaseURL = os.getenv("DATABASE_URL")

engine = create_async_engine(databaseURL, echo = True, connect_args = {"statement_cache_size": 0})
async_session = async_sessionmaker(engine, expire_on_commit = False)

async def get_db():
    async with async_session() as session:
        yield session