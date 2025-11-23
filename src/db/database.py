from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from .config import settings



engine = create_async_engine(
    url=settings.DATABASE_URL,
    echo=True
)

session = async_sessionmaker(engine)

class Base(DeclarativeBase):
    pass


async def create_tables():
    async with engine.begin() as conn:
        from sqlalchemy import text
        from . import models
        
        await conn.execute(text("DROP TABLE IF EXISTS choices CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS choice CASCADE"))
        await conn.execute(text("DROP TABLE IF EXISTS questions CASCADE"))
        
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)