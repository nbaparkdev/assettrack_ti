import asyncio
from sqlalchemy import select
from app.database import SessionLocal
from app.models.user import User
from app.models.asset import Asset, AssetStatus
from app.models.transaction import Movimentacao, TipoMovimentacao
from datetime import datetime

async def debug_baixa():
    async with SessionLocal() as db:
        print("Starting Debug Baixa...")
        
        # 1. Get an asset that is NOT already baixado
        result = await db.execute(select(Asset).filter(Asset.status != AssetStatus.BAIXADO).limit(1))
        asset = result.scalars().first()
        if not asset:
            print("No active asset found.")
            return

        # 2. Get an admin user (simulated)
        result = await db.execute(select(User).limit(1))
        current_user = result.scalars().first()
        
        print(f"Asset: {asset.id} ({asset.nome}) - Status: {asset.status}")
        print(f"User (Admin): {current_user.id} ({current_user.nome})")

        # 3. Simulate Write-off logic
        try:
            previous_user = asset.current_user_id
            
            # Update Asset
            asset.status = AssetStatus.BAIXADO
            asset.current_user_id = None
            
            print("Asset updated (in memory).")
            
            # Create Movement
            movimentacao = Movimentacao(
                asset_id=asset.id,
                tipo=TipoMovimentacao.BAIXA,
                de_user_id=previous_user,
                para_user_id=None, # Gone
                data=datetime.now(),
                observacao=f"Baixa efetuada por {current_user.nome}"
            )
            
            print("Adding to DB (dry run - rolling back)...")
            db.add(asset)
            db.add(movimentacao)
            await db.flush() 
            print("Flush successful!")
            
            await db.rollback()
            print("Rollback successful. Logic seems valid.")
            
        except Exception as e:
            print(f"ERROR CAUGHT: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_baixa())
