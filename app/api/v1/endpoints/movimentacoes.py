
# app/api/v1/endpoints/movimentacoes.py
from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import dependencies
from app.crud import transaction as transaction_crud
from app.crud import asset as asset_crud
from app.schemas.transaction import MovimentacaoResponse, MovimentacaoCreate
from app.models.transaction import TipoMovimentacao
from app.models.asset import AssetStatus
from app.database import get_db

router = APIRouter()

@router.get("/", response_model=List[MovimentacaoResponse])
async def read_movimentacoes(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dependencies.User, Depends(dependencies.get_current_active_user)],
    skip: int = 0,
    limit: int = 100,
    asset_id: int = None
):
    if asset_id:
        return await transaction_crud.movimentacao.get_by_asset(db, asset_id=asset_id)
    return await transaction_crud.movimentacao.get_multi(db, skip=skip, limit=limit)

@router.post("/devolver/{asset_id}", response_model=MovimentacaoResponse)
async def devolver_asset(
    asset_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dependencies.User, Depends(dependencies.get_current_active_user)], 
    # Idealmente, qualquer um pode devolver? ou só gerente recebe? 
    # Vamos assumir que gerente recebe a devolução ou o proprio usuário inicia a devolução e fica pendente.
    # Simplificando: Gerente registra a devolução.
):
    # Verifica permissão (apenas gerente/admin devolve ao estoque por enquanto para garantir conferencia)
    # Se usuário_comum puder, teria que ser "Solicitar Devolução"
    if current_user.role == dependencies.UserRole.USUARIO:
         raise HTTPException(status_code=403, detail="Apenas gerentes podem confirmar devolução imediata.")

    asset = await asset_crud.asset.get(db, id=asset_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Asset não encontrado")

    if asset.status == AssetStatus.DISPONIVEL:
        raise HTTPException(status_code=400, detail="Asset já está disponível")

    # Registra movimentação
    mov = dependencies.Movimentacao(
        asset_id=asset.id,
        tipo=TipoMovimentacao.DEVOLUCAO,
        de_user_id=asset.current_user_id,
        para_user_id=None, # Devolveu para "Estoque" (sem user)
        # de_departamento...
        observacao="Devolução registrada manualmente"
    )
    
    # Atualiza Asset
    asset.status = AssetStatus.DISPONIVEL
    asset.current_user_id = None
    # Definir local de armazenamento padrão ou deixar null para preencher depois
    
    db.add(mov)
    db.add(asset)
    await db.commit()
    await db.refresh(mov)
    return mov
