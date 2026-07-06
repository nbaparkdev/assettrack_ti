import asyncio
from app.database import SessionLocal
from app.services.email_service import EmailService

async def test():
    async with SessionLocal() as db:
        svc = EmailService()
        result = await svc.send_notification(
            "test@example.com",
            "Teste Script",
            "Mensagem",
            db
        )
        print("Resultado do send_notification:", result)

if __name__ == "__main__":
    asyncio.run(test())
