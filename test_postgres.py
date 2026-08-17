import asyncio
import os
import sys

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.crud.system_settings import system_settings
from app.models.email_log import EmailLog

DATABASE_URL = "postgresql+asyncpg://user:password@localhost:5456/assettrack"

engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = async_sessionmaker(bind=engine)

async def test():
    async with SessionLocal() as db:
        print("Buscando configurações SMTP...")
        host = await system_settings.get_setting(db, "smtp_host", "NOT_FOUND")
        print("SMTP HOST:", host)

        print("Testando inserção de log...")
        try:
            log = EmailLog(
                recipient="test@example.com",
                subject="Test Subject",
                body="Test Body",
                status="SUCCESS",
                error_message=None
            )
            db.add(log)
            await db.commit()
            print("LOG INSERIDO COM SUCESSO!")
        except Exception as e:
            print("ERRO AO INSERIR LOG:", str(e))
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
