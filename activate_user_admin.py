import asyncio
from app.database import SessionLocal
from app.models.user import User
from sqlalchemy import update

async def activate_admin():
    async with SessionLocal() as db:
        stmt = update(User).where(User.email == "admin@example.com").values(is_active=True)
        await db.execute(stmt)
        await db.commit()
        print("Admin user activated: admin@example.com")

if __name__ == "__main__":
    asyncio.run(activate_admin())
