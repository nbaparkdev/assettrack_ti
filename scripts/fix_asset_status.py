import asyncio
import os
import sys
from sqlalchemy import select, or_

# Adicionar diretório raiz ao path
sys.path.append(os.getcwd())

from app.database import SessionLocal
from app.models.asset import Asset, AssetStatus
from app.models.user import User

async def fix_asset_statuses():
    async with SessionLocal() as db:
        print("🔍 Verificando ativos em estado inconsistente...")
        
        # Buscar ativos que têm usuário definido mas estão marcados como DISPONIVEL
        # Ou ativos que estão marcados como MANUTENCAO mas já têm usuário (o que seria estranho, mas possível)
        # O foco principal é: Status=DISPONIVEL + current_user_id != NULL
        
        query = select(Asset).filter(
            Asset.status == AssetStatus.DISPONIVEL,
            Asset.current_user_id.isnot(None)
        )
        
        result = await db.execute(query)
        assets = result.scalars().all()
        
        if not assets:
            print("✅ Nenhum ativo inconsistente encontrado.")
            return

        print(f"⚠️ Encontrados {len(assets)} ativos inconsistentes (Disponível + Com Usuário). Corrigindo...")
        
        for asset in assets:
            old_status = asset.status
            asset.status = AssetStatus.EM_USO
            print(f"  -> Ativo ID {asset.id} ({asset.nome}): {old_status} -> {asset.status} (Usuário ID: {asset.current_user_id})")
            db.add(asset)
            
        await db.commit()
        print("✅ Correção concluída com sucesso!")

if __name__ == "__main__":
    asyncio.run(fix_asset_statuses())
