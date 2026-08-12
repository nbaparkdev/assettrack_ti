import asyncio
from app.database import engine, Base
from app.models import Webhook, WebhookLog

async def create_tables():
    async with engine.begin() as conn:
        print("Creating Webhook tables...")
        await conn.run_sync(Base.metadata.create_all)
        print("Done.")

if __name__ == "__main__":
    asyncio.run(create_tables())
