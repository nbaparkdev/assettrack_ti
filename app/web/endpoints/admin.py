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

# Dependency to check staff role (includes technician)
async def check_staff_role(current_user: Annotated[User, Depends(get_active_user_web)]):
    if current_user.role not in [UserRole.ADMIN, UserRole.GERENTE, UserRole.TECNICO]:
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
    admin: Annotated[User, Depends(check_staff_role)]
):
    solicitacao = await db.get(Solicitacao, solicitacao_id)
    if not solicitacao or solicitacao.status != StatusSolicitacao.PENDENTE:
        raise HTTPException(status_code=404, detail="Solicitação inválida")
    
    asset = await db.get(Asset, solicitacao.asset_id)
    if not asset or asset.status not in [AssetStatus.DISPONIVEL, AssetStatus.EM_USO]:
         raise HTTPException(status_code=400, detail="Ativo indisponível para movimentação")

    # Update Solicitation
    solicitacao.status = StatusSolicitacao.APROVADA
    solicitacao.aprovador_id = admin.id
    solicitacao.data_aprovacao = datetime.utcnow()
    
    # Update Asset Status (Already Reserved/ARMAZENADO, now keep it that way until delivery)
    asset.status = AssetStatus.ARMAZENADO
    # Optionally: asset.current_user_id = None (it's with IT)

    await db.commit()
    return RedirectResponse(url="/", status_code=303)

@router.post("/solicitacoes/{solicitacao_id}/reject")
async def reject_solicitacao(
    solicitacao_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(check_staff_role)]
):
    solicitacao = await db.get(Solicitacao, solicitacao_id)
    if not solicitacao:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada")
    
    solicitacao.status = StatusSolicitacao.REJEITADA
    solicitacao.aprovador_id = admin.id
    solicitacao.data_aprovacao = datetime.utcnow()
    
    await db.commit()
    return RedirectResponse(url="/", status_code=303)

# -------------------------------------------------------------------------
# DELIVERY VALIDATION (QR CODE)
# -------------------------------------------------------------------------
from fastapi import Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import selectinload

templates = Jinja2Templates(directory="app/templates")

@router.get("/solicitacoes/{solicitacao_id}/entrega", response_class=RedirectResponse)
async def deliver_solicitacao_page(
    request: Request,
    solicitacao_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(check_staff_role)]
):
    # Eager load needed relations
    stmt = (
        select(Solicitacao)
        .options(selectinload(Solicitacao.asset), selectinload(Solicitacao.solicitante))
        .where(Solicitacao.id == solicitacao_id)
    )
    result = await db.execute(stmt)
    solicitacao = result.scalar_one_or_none()
    
    if not solicitacao or solicitacao.status != StatusSolicitacao.APROVADA:
        # If not approved, can't deliver.
        # Use HTMLResponse if we want to show error page, but Redirect is safer for now if invalid usage
        raise HTTPException(status_code=400, detail="Solicitação inválida ou não aprovada")

    return templates.TemplateResponse("admin/confirmar_entrega_asset.html", {
        "request": request,
        "user": current_user,
        "solicitacao": solicitacao,
        "title": f"Validar Entrega - #{solicitacao_id}"
    })

@router.post("/solicitacoes/{solicitacao_id}/entrega")
async def deliver_solicitacao_submit(
    request: Request,
    solicitacao_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(check_staff_role)],
    qr_token: Annotated[str, Form()] = "",
    observacao: Annotated[str, Form()] = ""
):
    # Import service singleton and Enum directly
    from app.services.notification_service import notification_service
    from app.models.transaction import TipoMovimentacao

    # Fetch Solicitation
    stmt = (
        select(Solicitacao)
        .options(selectinload(Solicitacao.asset), selectinload(Solicitacao.solicitante))
        .where(Solicitacao.id == solicitacao_id)
    )
    result = await db.execute(stmt)
    solicitacao = result.scalar_one_or_none()

    if not solicitacao or solicitacao.status != StatusSolicitacao.APROVADA:
        raise HTTPException(status_code=400, detail="Solicitação não está pronta para entrega")

    # Validate QR Code
    stmt_user = select(User).where(User.qr_token == qr_token.strip())
    result_user = await db.execute(stmt_user)
    qr_user = result_user.scalar_one_or_none()

    if not qr_user or qr_user.id != solicitacao.solicitante_id:
        # Return to form with error
        return templates.TemplateResponse("admin/confirmar_entrega_asset.html", {
            "request": request,
            "user": current_user,
            "solicitacao": solicitacao,
            "error": "QR Code inválido! Não pertence ao solicitante.",
            "title": f"Erro Entrega - #{solicitacao_id}"
        })

    # PROCEED WITH DELIVERY
    solicitacao.status = StatusSolicitacao.ENTREGUE
    solicitacao.data_entrega = datetime.utcnow()
    solicitacao.confirmado_por_id = current_user.id
    solicitacao.confirmado_via_qr = True
    solicitacao.observacao_entrega = observacao
    
    movimentacao = Movimentacao(
        asset_id=solicitacao.asset_id,
        tipo=TipoMovimentacao.EMPRESTIMO, # Assuming loan
        para_user_id=solicitacao.solicitante_id,
        de_user_id=current_user.id, # Delivered by Tech
        observacao=f"Entrega via QR Code (Solicitação #{solicitacao.id}). Obs: {observacao}"
    )
    db.add(movimentacao)

    # Update Asset
    asset = solicitacao.asset
    asset.status = AssetStatus.EM_USO
    asset.current_user_id = solicitacao.solicitante_id

    await db.commit()
    
    # Notify (Reusing notify_delivery_completed logic loosely or just sending email)
    # Since we are Admin/Tech delivering, maybe notify Managers?
    # Or just log it. The requirement implies notification like Maintenance.
    # Maintenance notifies Admin/Gerente about Tech delivery.
    # Here Tech/Admin delivers. We should notify other Admins/Gerentes.
    
    await notification_service.notify_delivery_completed(
        db=db,
        request_id=solicitacao.id,
        asset_name=asset.nome,
        requester_name=solicitacao.solicitante.nome,
        technician_name=current_user.nome,
        observation=observacao
    )

    return RedirectResponse(url="/", status_code=303)
