
# app/api/v1/endpoints/solicitacoes.py
from typing import Annotated, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import dependencies
from app.crud import transaction as transaction_crud
from app.crud import asset as asset_crud
from app.schemas.transaction import (
    SolicitacaoCreate, SolicitacaoUpdate, SolicitacaoResponse, MovimentacaoCreate
)
from app.models.transaction import StatusSolicitacao, TipoMovimentacao
from app.database import get_db

router = APIRouter()

@router.post("/", response_model=SolicitacaoResponse)
async def create_solicitacao(
    solicitacao_in: SolicitacaoCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dependencies.User, Depends(dependencies.get_current_active_user)],
):
    # Força o solicitante ser o usuário atual
    # Cria o objeto manualmente para injetar o solicitante_id
    # SolicitacaoCreate não tem solicitante_id, vamos adicionar no model_dump
    solicitacao_data = solicitacao_in.model_dump()
    db_obj = transaction_crud.Solicitacao(
        **solicitacao_data,
        solicitante_id=current_user.id
    )
    db.add(db_obj)
    await db.commit()
    await db.refresh(db_obj)
    return db_obj

@router.get("/", response_model=List[SolicitacaoResponse])
async def read_solicitacoes(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dependencies.User, Depends(dependencies.get_current_active_user)],
    skip: int = 0,
    limit: int = 100,
    pending_only: bool = False
):
    # Se usuário comum, vê só as suas
    if current_user.role == dependencies.UserRole.USUARIO:
        return await transaction_crud.solicitacao.get_by_user(db, user_id=current_user.id)
    
    # Se gerente/admin
    if pending_only:
        return await transaction_crud.solicitacao.get_pending(db)
    
    return await transaction_crud.solicitacao.get_multi(db, skip=skip, limit=limit)

@router.put("/{solicitacao_id}/approve", response_model=SolicitacaoResponse)
async def approve_solicitacao(
    solicitacao_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dependencies.User, Depends(dependencies.get_current_active_manager_or_superuser)],
):
    solicitacao = await transaction_crud.solicitacao.get(db, id=solicitacao_id)
    if not solicitacao:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada")
    
    if solicitacao.status != StatusSolicitacao.PENDENTE:
         raise HTTPException(status_code=400, detail="Solicitação não está pendente")
         
    if not solicitacao.asset_id:
        raise HTTPException(status_code=400, detail="Solicitação não tem asset vinculado para aprovar. Vincule antes.")

    asset = await asset_crud.asset.get(db, id=solicitacao.asset_id)
    if not asset:
         raise HTTPException(status_code=404, detail="Asset não existe mais")
         
    # Atualiza Solicitação
    solicitacao.status = StatusSolicitacao.APROVADA
    solicitacao.aprovador_id = current_user.id
    solicitacao.data_aprovacao = datetime.utcnow()
    
    # Atualiza Asset e cria Movimentação (Lógica de negócio aqui)
    # Lógica: Se aprovou empréstimo, asset vai para o usuário
    
    # 1. Cria Movimentação de Saída (Empréstimo)
    mov = dependencies.Movimentacao(
        asset_id=asset.id,
        tipo=TipoMovimentacao.EMPRESTIMO,
        de_user_id=asset.current_user_id, # Quem estava com ele antes (ou None se estoque)
        para_user_id=solicitacao.solicitante_id,
        de_departamento_id=asset.current_departamento_id,
        para_departamento_id=solicitacao.solicitante.departamento_id if solicitacao.solicitante else None, # Assumindo carregado
        observacao=f"Aprovação de solicitação #{solicitacao.id}"
    )
    db.add(mov)

    # 2. Atualiza Asset
    asset.status = dependencies.AssetStatus.EM_USO
    asset.current_user_id = solicitacao.solicitante_id
    # Limpa dep/local se for para usuário, ou mantem? Geralmente asset em uso fica com user.
    # asset.current_local_id = ... (opcional)
    
    db.add(asset)
    db.add(solicitacao)
    await db.commit()
    await db.refresh(solicitacao)
    return solicitacao

@router.put("/{solicitacao_id}/reject", response_model=SolicitacaoResponse)
async def reject_solicitacao(
    solicitacao_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dependencies.User, Depends(dependencies.get_current_active_manager_or_superuser)],
):
    solicitacao = await transaction_crud.solicitacao.get(db, id=solicitacao_id)
    if not solicitacao:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada")
        
    solicitacao.status = StatusSolicitacao.REJEITADA
    solicitacao.aprovador_id = current_user.id
    solicitacao.data_aprovacao = datetime.utcnow()
    
    db.add(solicitacao)
    await db.commit()
    await db.refresh(solicitacao)
    return solicitacao
