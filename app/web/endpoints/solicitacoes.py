
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
    assets = await asset_crud.asset.get_multi(db)
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
    try:
        solicitation_data = {
            "asset_id": asset_id,
            "solicitante_id": current_user.id,
            "motivo": reason,
            "status": StatusSolicitacao.PENDENTE
        }
        await transaction_crud.solicitacao.create(db, obj_in=solicitation_data)
        return RedirectResponse(url="/solicitacoes", status_code=303)
    except Exception as e:
        assets = await asset_crud.asset.get_multi(db)
        return templates.TemplateResponse("solicitacoes/form.html", {
            "request": request,
            "user": current_user,
            "assets": assets,
            "error": f"Erro ao criar solicitação: {str(e)}",
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
