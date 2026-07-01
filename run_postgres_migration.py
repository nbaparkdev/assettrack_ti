import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    # Conecta no Postgres através da porta 5455 exposta pelo docker-compose
    database_url = "postgresql+asyncpg://user:password@localhost:5455/assettrack"
    engine = create_async_engine(database_url)
    
    print("Conectando ao banco de dados em localhost:5455...")
    async with engine.begin() as conn:
        try:
            await conn.execute(text("ALTER TABLE maintenance_materials ADD COLUMN product_id INTEGER REFERENCES purchase_products(id)"))
            print("Sucesso: Coluna 'product_id' adicionada com sucesso à tabela 'maintenance_materials'!")
        except Exception as e:
            print(f"Erro ao executar migration: {e}")

if __name__ == "__main__":
    asyncio.run(main())
