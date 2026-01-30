
import asyncio
from app.database import SessionLocal
from app.crud.user import user as user_crud
from app.schemas.user import UserCreate
from app.models.user import UserRole
import sys

async def create_tecnico():
    async with SessionLocal() as db:
        email = "tecnico@example.com"
        password = "123"
        
        existing_user = await user_crud.get_by_email(db, email=email)
        if existing_user:
            print(f"User {email} already exists.")
            # Ensure it is a technician
            if existing_user.role != UserRole.TECNICO:
                print(f"Updating role for {email} to TECNICO")
                # Direct SQL update or crud update needed if we want to change role
                # For simplicity in this script, just notifying
                print("WARNING: Existing user is not TECNICO. Please update manually or delete user.")
            return

        user_in = UserCreate(
            email=email,
            password=password,
            nome="Técnico de Suporte",
            role=UserRole.TECNICO,
            matricula="TEC001",
            cargo="Técnico N1"
        )
        await user_crud.create(db, obj_in=user_in)
        print(f"Technician created: {email} / {password}")

if __name__ == "__main__":
    asyncio.run(create_tecnico())
