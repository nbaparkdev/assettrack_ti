import asyncio
import sys
from app.database import SessionLocal
from app.models.user import User, UserRole
from sqlalchemy import select

async def main(email: str):
    async with SessionLocal() as db:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalars().first()
        
        if not user:
            print(f"Usuário com email {email} não encontrado no banco de dados!")
            return
            
        print(f"Usuário encontrado: {user.email}, Role atual: {user.role}")
        user.role = UserRole.COMPRADOR
        print(f"Mudando o cargo de {user.email} para COMPRADOR...")
        
        await db.commit()
        
        # Verify
        result = await db.execute(select(User).where(User.email == email))
        updated_user = result.scalars().first()
        if updated_user:
            print(f"Sucesso! O usuário {updated_user.email} agora tem o cargo: {updated_user.role}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Por favor, informe o email do usuário. Exemplo:")
        print("python app/set_comprador.py juarez@nba.com")
    else:
        asyncio.run(main(sys.argv[1]))
