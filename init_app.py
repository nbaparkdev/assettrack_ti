#!/usr/bin/env python3
import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.database import engine, Base
from app.models import User
from sqlalchemy import select, text
from passlib.context import CryptContext


async def init_database():
    print("🔧 Criando tabelas no banco de dados...")
    
    # Criar todas as tabelas (incluindo as de Manutenção Preventiva)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
        # Garantir que a coluna requer_termo_rh existe na tabela assets
        try:
            await conn.execute(text("ALTER TABLE assets ADD COLUMN requer_termo_rh BOOLEAN DEFAULT FALSE"))
            print("🔧 Adicionada coluna 'requer_termo_rh' na tabela 'assets'...")
        except Exception:
            try:
                await conn.execute(text("ALTER TABLE assets ADD COLUMN requer_termo_rh BOOLEAN DEFAULT 0"))
                print("🔧 Adicionada coluna 'requer_termo_rh' na tabela 'assets' (fallback)...")
            except Exception:
                pass

        # Garantir que a coluna aprovado existe na tabela purchase_research_items
        try:
            await conn.execute(text("ALTER TABLE purchase_research_items ADD COLUMN aprovado BOOLEAN DEFAULT TRUE"))
            print("🔧 Adicionada coluna 'aprovado' na tabela 'purchase_research_items'...")
        except Exception:
            pass
    
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


async def seed_maintenance_types():
    print("🔧 Semeando tipos de manutenção padrão...")
    from app.models.preventive_maintenance import CustomMaintenanceType, MaintenanceType
    from app.core.datetime_utils import now_sp
    from sqlalchemy.ext.asyncio import AsyncSession
    
    async with AsyncSession(engine) as db:
        result = await db.execute(select(CustomMaintenanceType))
        if not result.scalars().first():
            for mt in MaintenanceType:
                db.add(CustomMaintenanceType(
                    nome=mt.value,
                    descricao="Tipo padrão do sistema",
                    criado_em=now_sp()
                ))
            await db.commit()
            print("✅ Tipos de manutenção padrão semeados!")
        else:
            print("ℹ️ Tipos de manutenção já existem, pulando semeadura.")


async def sync_sequences():
    """Reset PostgreSQL sequences to max(id) for all tables that use serial PKs.
    This prevents duplicate key violations when rows were inserted outside
    normal ORM flows (e.g. direct SQL inserts, manual seeding, restores)."""
    print("🔧 Sincronizando sequências de IDs do banco de dados...")
    tables = [
        "users", "assets", "system_settings", "email_logs",
        "maintenance_requests", "maintenance_orders", "custom_maintenance_types",
        "maintenance_plans", "maintenance_materials", "maintenance_executions",
        "purchase_products", "purchase_requests", "purchase_orders",
        "service_desk_tickets", "contracts", "suppliers",
    ]
    async with engine.begin() as conn:
        for table in tables:
            try:
                await conn.execute(text(
                    f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), "
                    f"coalesce(max(id), 1), max(id) IS NOT NULL) FROM {table};"
                ))
            except Exception:
                pass  # Table may not exist yet — skip silently
    print("✅ Sequências sincronizadas!")


async def main():
    print("=" * 50)
    print("  AssetTrack TI - Inicialização do Sistema")
    print("=" * 50)
    print()
    
    try:
        await init_database()
        print()
        await sync_sequences()
        print()
        await create_admin_user()
        print()
        await seed_maintenance_types()
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
