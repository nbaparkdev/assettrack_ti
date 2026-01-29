from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.web.dependencies import get_active_user_web
from app.models.user import User, UserRole
from app.models.transaction import Solicitacao, StatusSolicitacao, Movimentacao, TipoMovimentacao
from app.models.asset import Asset, AssetStatus
from datetime import datetime

router = APIRouter()

# Dependency to check admin/manager role
async def check_admin_role(current_user: Annotated[User, Depends(get_active_user_web)]):
    if current_user.role not in [UserRole.ADMIN, UserRole.GERENTE]:
        raise HTTPException(status_code=403, detail="Acesso negado")
    return current_user

@router.post("/users/{user_id}/approve")
async def approve_user(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(check_admin_role)]
):
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    user.is_active = True
    await db.commit()
    return RedirectResponse(url="/", status_code=303)

@router.post("/solicitacoes/{solicitacao_id}/approve")
async def approve_solicitacao(
    solicitacao_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(check_admin_role)]
):
    solicitacao = await db.get(Solicitacao, solicitacao_id)
    if not solicitacao or solicitacao.status != StatusSolicitacao.PENDENTE:
        raise HTTPException(status_code=404, detail="Solicitação inválida")
    
    asset = await db.get(Asset, solicitacao.asset_id)
    if not asset or asset.status != AssetStatus.DISPONIVEL:
         raise HTTPException(status_code=400, detail="Ativo indisponível")

    # Update Solicitation
    solicitacao.status = StatusSolicitacao.APROVADA
    solicitacao.aprovador_id = admin.id
    solicitacao.data_aprovacao = datetime.utcnow()
    
    # Create Movement (Saída)
    movimentacao = Movimentacao(
        asset_id=asset.id,
        tipo=TipoMovimentacao.EMPRESTIMO,
        para_user_id=solicitacao.solicitante_id,
        de_user_id=admin.id, # Quem aprovou é a origem lógica da entrega
        observacao=f"Solicitação aprovada por {admin.nome}"
    )
    db.add(movimentacao)

    # Update Asset Status
    asset.status = AssetStatus.EM_USO
    asset.current_user_id = solicitacao.solicitante_id

    await db.commit()
    return RedirectResponse(url="/", status_code=303)

@router.post("/solicitacoes/{solicitacao_id}/reject")
async def reject_solicitacao(
    solicitacao_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(check_admin_role)]
):
    solicitacao = await db.get(Solicitacao, solicitacao_id)
    if not solicitacao:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada")
    
    solicitacao.status = StatusSolicitacao.REJEITADA
    solicitacao.aprovador_id = admin.id
    solicitacao.data_aprovacao = datetime.utcnow()
    
    await db.commit()
    return RedirectResponse(url="/", status_code=303)
