
import asyncio
from app.database import SessionLocal
from app.crud.user import user as user_crud
from app.schemas.user import UserCreate
from app.models.user import UserRole
from app.api.dependencies import get_current_active_manager_or_superuser, get_db

async def create_superuser():
    async with SessionLocal() as db:
        admin_email = "admin@example.com"
        admin_password = "admin"
        
        existing_user = await user_crud.get_by_email(db, email=admin_email)
        if existing_user:
            print(f"User {admin_email} already exists.")
            return

        user_in = UserCreate(
            email=admin_email,
            password=admin_password,
            nome="Administrador",
            role=UserRole.ADMIN,
            matricula="AAAA001",
            cargo="Super Admin"
        )
        await user_crud.create(db, obj_in=user_in)
        print(f"Superuser created: {admin_email} / {admin_password}")

if __name__ == "__main__":
    asyncio.run(create_superuser())
