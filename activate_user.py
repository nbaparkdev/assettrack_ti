import asyncio
import sys
from app.database import SessionLocal
from app.models.user import User
from sqlalchemy import select

async def activate_user(email=None):
    async with SessionLocal() as db:
        if email:
            # Ativa um usuário específico
            result = await db.execute(select(User).filter(User.email == email))
            user = result.scalars().first()
            if not user:
                print(f"Erro: Usuário com email '{email}' não encontrado.")
                return
            
            user.is_active = True
            print(f"Usuário {email} ativado com sucesso!")
        else:
            # Ativa todos os usuários pendentes
            result = await db.execute(select(User).filter(User.is_active == False))
            users = result.scalars().all()
            if not users:
                print("Nenhum usuário pendente para ativação.")
                return
            
            for user in users:
                user.is_active = True
                print(f"Usuário {user.email} ativado.")
            
            print(f"Total de {len(users)} usuários ativados.")
            
        await db.commit()

if __name__ == "__main__":
    email_arg = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(activate_user(email_arg))
