import asyncio
from app.database import SessionLocal
from sqlalchemy import text

async def main():
    async with SessionLocal() as db:
        print("Sincronizando a sequência de IDs da tabela 'users'...")
        try:
            # Resync id sequence for users table in Postgres
            await db.execute(text("SELECT setval(pg_get_serial_sequence('users', 'id'), coalesce(max(id), 1), max(id) IS NOT null) FROM users;"))
            await db.commit()
            print("Sequência 'users_id_seq' sincronizada com sucesso!")
        except Exception as e:
            print(f"Erro ao sincronizar sequência: {e}")

if __name__ == "__main__":
    asyncio.run(main())
