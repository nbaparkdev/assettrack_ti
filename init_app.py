#!/usr/bin/env python3
import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.database import engine, Base
from app.models import User
from sqlalchemy import select
from passlib.context import CryptContext


async def init_database():
    print("🔧 Criando tabelas no banco de dados...")
    
    # Criar todas as tabelas (incluindo as de Manutenção Preventiva)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    print("✅ Tabelas criadas!")


async def create_admin_user():
    print("🔧 Criando/Ativando usuário admin...")
    
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    hashed_password = pwd_context.hash("admin")
    
    from app.database import get_db
    from sqlalchemy.ext.asyncio import AsyncSession
    
    async with AsyncSession(engine) as db:
        # Verificar se o usuário já existe
        result = await db.execute(select(User).filter(User.email == "admin@example.com"))
        user = result.scalars().first()
        
        if not user:
            # Criar novo usuário admin
            new_user = User(
                email="admin@example.com",
                nome="Administrador",
                hashed_password=hashed_password,
                role="ADMIN",
                is_active=True
            )
            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)
            print("✅ Usuário admin criado com sucesso!")
            print("   Email: admin@example.com")
            print("   Senha: admin")
        else:
            # Ativar usuário existente
            user.is_active = True
            await db.commit()
            print("✅ Usuário admin ativado com sucesso!")
            print("   Email: admin@example.com")
            print("   Senha: admin")


async def main():
    print("=" * 50)
    print("  AssetTrack TI - Inicialização do Sistema")
    print("=" * 50)
    print()
    
    try:
        await init_database()
        print()
        await create_admin_user()
        print()
        print("=" * 50)
        print("  ✅ Inicialização concluída com sucesso!")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Erro durante a inicialização: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
