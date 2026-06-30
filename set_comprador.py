import asyncio
from app.database import SessionLocal
from app.models.user import User, UserRole
from sqlalchemy import select

async def main():
    async with SessionLocal() as db:
        result = await db.execute(select(User))
        users = result.scalars().all()
        for u in users:
            print(f"User: {u.email}, Role: {u.role}")
            if u.email == "admin@example.com":
                u.role = UserRole.COMPRADOR
                print(f"Changing {u.email} to COMPRADOR role.")
        
        await db.commit()
        
        # Verify
        result = await db.execute(select(User).where(User.email == "admin@example.com"))
        admin = result.scalars().first()
        if admin:
            print(f"Verified {admin.email} is now: {admin.role}")
        else:
            print("Admin user not found.")

if __name__ == "__main__":
    asyncio.run(main())
