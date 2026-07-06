import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select
import sys
import os

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.email_log import EmailLog
from app.crud.system_settings import system_settings

DATABASE_URL = "postgresql+asyncpg://user:password@localhost:5455/assettrack"

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
