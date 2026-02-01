
# app/web/endpoints/solicitacoes.py
from typing import Annotated, Optional
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import datetime

from app.web.dependencies import get_active_user_web
from app.models.user import User, UserRole
from app.models.transaction import Solicitacao, StatusSolicitacao
from app.database import get_db
from app.crud import transaction as transaction_crud
from app.crud import asset as asset_crud
from app.models.asset import Asset, AssetStatus

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def list_solicitacoes(
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    if current_user.role == UserRole.USUARIO:
        solicitacoes = await transaction_crud.solicitacao.get_by_user(db, user_id=current_user.id)
    else:
        solicitacoes = await transaction_crud.solicitacao.get_multi(db)
    return templates.TemplateResponse("solicitacoes/list.html", {
        "request": request,
        "user": current_user,
        "solicitacoes": solicitacoes,
        "title": "Minhas Solicitações"
    })

# Static routes BEFORE dynamic routes
@router.get("/new", response_class=HTMLResponse)
async def new_solicitacao_form(
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    # Only fetch AVAILABLE assets
    result = await db.execute(
        select(Asset)
        .filter(Asset.status == AssetStatus.DISPONIVEL)
        .order_by(Asset.nome)
    )
    assets = result.scalars().all()
    
    return templates.TemplateResponse("solicitacoes/form.html", {
        "request": request,
        "user": current_user,
        "assets": assets,
        "title": "Nova Solicitação"
    })

@router.post("/new", response_class=HTMLResponse)
async def create_solicitacao(
    request: Request,
    asset_id: Annotated[int, Form()],
    reason: Annotated[str, Form()],
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    # Re-fetch assets for error context if needed
    async def get_available_assets():
        res = await db.execute(
            select(Asset)
            .filter(Asset.status == AssetStatus.DISPONIVEL)
            .order_by(Asset.nome)
        )
        return res.scalars().all()

    try:
        # Check if asset is actually available (concurrency check)
        asset_result = await db.execute(select(Asset).filter(Asset.id == asset_id))
        target_asset = asset_result.scalar_one_or_none()
        
        if not target_asset:
            raise Exception("Ativo não encontrado.")
            
        if target_asset.status != AssetStatus.DISPONIVEL:
            # Check reasons for unavailability
            msg = "Ativo indisponível para solicitação."
            if target_asset.current_user_id == current_user.id:
                msg = "Você já possui este ativo (está em seu uso)."
            elif target_asset.status == AssetStatus.EM_USO:
                msg = "Este ativo já está em uso por outro usuário."
            elif target_asset.status == AssetStatus.MANUTENCAO:
                msg = "Este ativo está em manutenção."
                
            raise Exception(msg)

        solicitation_data = {
            "asset_id": asset_id,
            "solicitante_id": current_user.id,
            "motivo": reason,
            "status": StatusSolicitacao.PENDENTE
        }
        await transaction_crud.solicitacao.create(db, obj_in=solicitation_data)
        return RedirectResponse(url="/solicitacoes", status_code=303)
    except Exception as e:
        assets = await get_available_assets()
        return templates.TemplateResponse("solicitacoes/form.html", {
            "request": request,
            "user": current_user,
            "assets": assets,
            "error": f"Erro: {str(e)}",
            "title": "Nova Solicitação"
        })

@router.get("/admin", response_class=HTMLResponse)
async def list_solicitacoes_admin(
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    if current_user.role not in [UserRole.ADMIN, UserRole.GERENTE]:
        return RedirectResponse(url="/solicitacoes", status_code=303)

    pending_solicitacoes = await transaction_crud.solicitacao.get_pending(db)
    return templates.TemplateResponse("solicitacoes/admin_list.html", {
        "request": request,
        "user": current_user,
        "solicitacoes": pending_solicitacoes,
        "title": "Gerenciar Solicitações"
    })

# Dynamic routes AFTER static routes
@router.get("/{solicitacao_id}", response_class=HTMLResponse)
async def view_solicitacao(
    request: Request,
    solicitacao_id: int,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    result = await db.execute(
        select(Solicitacao)
        .options(selectinload(Solicitacao.asset), selectinload(Solicitacao.solicitante), selectinload(Solicitacao.aprovador))
        .filter(Solicitacao.id == solicitacao_id)
    )
    solicitacao = result.scalars().first()
    
    if not solicitacao:
        return RedirectResponse(url="/solicitacoes", status_code=303)
    
    return templates.TemplateResponse("solicitacoes/detail.html", {
        "request": request,
        "user": current_user,
        "sol": solicitacao,
        "title": f"Solicitação #{solicitacao_id}"
    })

@router.post("/{solicitacao_id}/approve", response_class=HTMLResponse)
async def approve_solicitacao(
    request: Request,
    solicitacao_id: int,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    if current_user.role not in [UserRole.ADMIN, UserRole.GERENTE]:
        return RedirectResponse(url="/solicitacoes", status_code=303)

    await transaction_crud.solicitacao.approve(db, solicitacao_id=solicitacao_id, aprovador_id=current_user.id)
    return RedirectResponse(url="/solicitacoes", status_code=303)

@router.post("/{solicitacao_id}/reject", response_class=HTMLResponse)
async def reject_solicitacao(
    request: Request,
    solicitacao_id: int,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    if current_user.role not in [UserRole.ADMIN, UserRole.GERENTE]:
        return RedirectResponse(url="/solicitacoes", status_code=303)

    await transaction_crud.solicitacao.reject(db, solicitacao_id=solicitacao_id, aprovador_id=current_user.id)
    return RedirectResponse(url="/solicitacoes", status_code=303)


@router.get("/{solicitacao_id}/confirmar-entrega", response_class=HTMLResponse)
async def confirmar_entrega_page(
    request: Request,
    solicitacao_id: int,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Página de confirmação de entrega - Admin/Gerente pode confirmar com ou sem QR do usuário"""
    if current_user.role not in [UserRole.ADMIN, UserRole.GERENTE]:
        return RedirectResponse(url="/solicitacoes", status_code=303)

    result = await db.execute(
        select(Solicitacao)
        .options(selectinload(Solicitacao.asset), selectinload(Solicitacao.solicitante))
        .filter(Solicitacao.id == solicitacao_id)
    )
    solicitacao = result.scalars().first()
    
    if not solicitacao or solicitacao.status != StatusSolicitacao.APROVADA:
        return RedirectResponse(url="/solicitacoes", status_code=303)
    
    return templates.TemplateResponse("solicitacoes/confirmar_entrega.html", {
        "request": request,
        "user": current_user,
        "sol": solicitacao,
        "title": f"Confirmar Entrega - #{solicitacao_id}"
    })


@router.post("/{solicitacao_id}/confirmar-entrega", response_class=HTMLResponse)
async def confirmar_entrega_submit(
    request: Request,
    solicitacao_id: int,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)],
    qr_token: Annotated[Optional[str], Form()] = None,
    observacao: Annotated[Optional[str], Form()] = None
):
    """Processa confirmação de entrega - valida QR do usuário se fornecido"""
    from app.crud import user as user_crud
    
    if current_user.role not in [UserRole.ADMIN, UserRole.GERENTE]:
        return RedirectResponse(url="/solicitacoes", status_code=303)

    result = await db.execute(
        select(Solicitacao)
        .options(selectinload(Solicitacao.asset), selectinload(Solicitacao.solicitante))
        .filter(Solicitacao.id == solicitacao_id)
    )
    solicitacao = result.scalars().first()
    
    if not solicitacao or solicitacao.status != StatusSolicitacao.APROVADA:
        return RedirectResponse(url="/solicitacoes?error=invalid_status", status_code=303)
    
    confirmado_via_qr = False
    
    # Validar QR Code se fornecido
    if qr_token and qr_token.strip():
        qr_user = await user_crud.user.get_by_qr_token(db, token=qr_token.strip())
        if not qr_user or qr_user.id != solicitacao.solicitante_id:
            # QR Code inválido ou não pertence ao solicitante
            return templates.TemplateResponse("solicitacoes/confirmar_entrega.html", {
                "request": request,
                "user": current_user,
                "sol": solicitacao,
                "error": "QR Code inválido ou não pertence ao solicitante!",
                "title": f"Confirmar Entrega - #{solicitacao_id}"
            })
        confirmado_via_qr = True
    
    # Atualizar solicitação
    solicitacao.status = StatusSolicitacao.ENTREGUE
    solicitacao.data_entrega = datetime.utcnow()
    solicitacao.confirmado_por_id = current_user.id
    solicitacao.confirmado_via_qr = confirmado_via_qr
    solicitacao.observacao_entrega = observacao

    # Enforce Asset Status to EM_USO (as requested by user)
    # Even if it was already set during approval, we reinforce it here upon physical delivery confirmation
    if solicitacao.asset:
        solicitacao.asset.status = AssetStatus.EM_USO
        solicitacao.asset.current_user_id = solicitacao.solicitante_id
        db.add(solicitacao.asset)
    
    await db.commit()
    
    return RedirectResponse(url=f"/solicitacoes/{solicitacao_id}?success=delivered", status_code=303)

