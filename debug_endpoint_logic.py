import asyncio
from app.database import SessionLocal
from app.crud import asset as asset_crud
from app.models.transaction import Solicitacao, StatusSolicitacao
from app.models.user import User
from sqlalchemy import select
from datetime import datetime

async def debug_endpoint():
    async with SessionLocal() as db:
        print("Starting Debug Endpoint Logic...")
        
        # 1. Test CRUDAsset.get (with eager loading)
        asset_id = 1
        print(f"Fetching Asset {asset_id} using asset_crud.asset.get...")
        try:
            asset = await asset_crud.asset.get(db, id=asset_id)
            if not asset:
                print("Asset not found.")
                return
            print(f"Asset found: {asset.nome}")
            # Access lazy field to ensure it is loaded
            print(f"Current User: {asset.current_user.nome if asset.current_user else 'None'}")
        except Exception as e:
            print(f"CRITICAL: CRUDAsset.get failed: {e}")
            import traceback
            traceback.print_exc()
            return

        # 2. Simulate Transfer Logic
        try:
            # Get a user to act as current_user
            result = await db.execute(select(User).limit(1))
            current_user = result.scalars().first()
            
            destinatario_id = 9999 # Non-existent, or just an int
            motivo = "Debug Reason Endpoint"
            
            print("Simulating Solicitation Creation...")
            solicitacao = Solicitacao(
                solicitante_id=current_user.id,
                asset_id=asset.id,
                motivo=f"[TRANSFERÊNCIA] Para user ID {destinatario_id}: {motivo}",
                status=StatusSolicitacao.PENDENTE,
                data_solicitacao=datetime.utcnow()
            )
            solicitacao.solicitante_id = destinatario_id
            solicitacao.motivo = f"Transferência solicitada por {current_user.nome}: {motivo}"
            
            db.add(solicitacao)
            # We won't commit to avoid junk, but we flush
            print("Flushing...")
            await db.flush()
            print("Flush successful.")
            await db.rollback()
            
        except Exception as e:
            print(f"CRITICAL: Endpoint logic failed: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_endpoint())
