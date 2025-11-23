from src.db.database import create_tables
import asyncio


async def main():
    await create_tables()

asyncio.run(main())