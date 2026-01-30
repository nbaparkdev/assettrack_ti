import asyncio
from sqlalchemy import select
from app.database import SessionLocal
from app.models.user import User
from app.models.asset import Asset
from app.models.transaction import Solicitacao, StatusSolicitacao
from datetime import datetime

async def debug_transfer():
    async with SessionLocal() as db:
        print("Starting Debug Transfer...")
        
        # 1. Get an asset
        result = await db.execute(select(Asset).limit(1))
        asset = result.scalars().first()
        if not asset:
            print("No asset found.")
            return

        # 2. Get two users
        result = await db.execute(select(User).limit(2))
        users = result.scalars().all()
        if len(users) < 2:
            print("Need at least 2 users.")
            return
        
        user_a = users[0]
        user_b = users[1]
        
        print(f"Asset: {asset.id} ({asset.nome})")
        print(f"User A (Requester): {user_a.id} ({user_a.nome})")
        print(f"User B (Target): {user_b.id} ({user_b.nome})")

        # 3. Simulate Transfer Request logic
        try:
            motivo = "Debug Reason"
            destinatario_id = user_b.id
            current_user = user_a

            print("Creating Solicitacao object...")
            solicitacao = Solicitacao(
                solicitante_id=current_user.id,
                asset_id=asset.id,
                motivo=f"[TRANSFERÊNCIA] Para user ID {destinatario_id}: {motivo}",
                status=StatusSolicitacao.PENDENTE,
                data_solicitacao=datetime.utcnow()
            )
            
            # The logic used in the endpoint
            solicitacao.solicitante_id = destinatario_id
            solicitacao.motivo = f"Transferência solicitada por {current_user.nome}: {motivo}"
            
            print("Adding to DB (dry run - rolling back)...")
            db.add(solicitacao)
            await db.flush() # Check for integrity errors
            print("Flush successful!")
            
            await db.rollback()
            print("Rollback successful. Logic seems valid.")
            
        except Exception as e:
            print(f"ERROR CAUGHT: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_transfer())
