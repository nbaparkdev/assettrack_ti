import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models.user import User

DATABASE_URL = "postgresql+asyncpg://user:password@localhost:5456/assettrack"

engine = create_async_engine(DATABASE_URL, echo=False)
SessionLocal = async_sessionmaker(bind=engine)

async def test():
    async with SessionLocal() as db:
        res = await db.execute(select(User).order_by(User.id))
        users = res.scalars().all()
        print(f"TOTAL USERS IN DB: {len(users)}")
        for u in users:
            print(f"ID: {u.id} | Nome: {u.nome} | Email: {u.email} | Role: {u.role.value if hasattr(u.role, 'value') else u.role} | Is Active: {u.is_active}")

if __name__ == "__main__":
    asyncio.run(test())
