# app/web/endpoints/service_desk.py
import os
from typing import Annotated, Optional
from datetime import datetime
from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.web.dependencies import get_active_user_web
from app.models.user import User, UserRole
from app.models.service_desk import ServiceCategory, ServiceDefinition, ServiceTicket, ServiceStatus, ServicePriority
from app.database import get_db
from app.crud import service_desk as service_desk_crud
from app.schemas.service_desk import ServiceTicketCreate, ServiceCategoryCreate, ServiceDefinitionCreate
from app.services.qr_service import QRService

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def service_desk_home(
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Página principal do Service Desk - Lista de chamados do usuário ou todos para admin/técnico"""
    user_role = str(current_user.role.value).lower()
    if user_role in [UserRole.ADMIN, UserRole.GERENTE, UserRole.TECNICO, UserRole.GERENTE_INFRA]:
        tickets = await service_desk_crud.ticket.search_tickets(db)
        stats = {
            "abertos": await db.scalar(select(func.count(ServiceTicket.id)).filter(ServiceTicket.status == ServiceStatus.ABERTO)),
            "em_atendimento": await db.scalar(select(func.count(ServiceTicket.id)).filter(ServiceTicket.status == ServiceStatus.EM_ATENDIMENTO)),
            "resolvidos": await db.scalar(select(func.count(ServiceTicket.id)).filter(ServiceTicket.status == ServiceStatus.RESOLVIDO))
        }
    else:
        tickets = await service_desk_crud.ticket.get_user_tickets(db, current_user.id)
        stats = None

    return templates.TemplateResponse("service_desk/list.html", {
        "request": request,
        "user": current_user,
        "tickets": tickets,
        "stats": stats,
        "title": "Service Desk"
    })

@router.get("/novo", response_class=HTMLResponse)
async def new_ticket_form(
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Formulário para abertura de novo chamado"""
    categories = await service_desk_crud.category.get_all_with_definitions(db)
    return templates.TemplateResponse("service_desk/form.html", {
        "request": request,
        "user": current_user,
        "categories": categories,
        "priorities": ServicePriority,
        "title": "Novo Chamado"
    })

@router.post("/novo")
async def create_ticket(
    request: Request,
    titulo: Annotated[str, Form()],
    servico_id: Annotated[int, Form()],
    prioridade: Annotated[str, Form()],
    descricao: Annotated[str, Form()],
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    ticket_in = ServiceTicketCreate(
        titulo=titulo,
        servico_id=servico_id,
        prioridade=ServicePriority(prioridade),
        descricao=descricao
    )
    ticket = await service_desk_crud.ticket.create_with_codigo(db, obj_in=ticket_in, solicitante_id=current_user.id)
    return RedirectResponse(url=f"/servicos/chamado/{ticket.id}", status_code=303)

@router.get("/chamado/{ticket_id}", response_class=HTMLResponse)
async def ticket_detail(
    request: Request,
    ticket_id: int,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    ticket = await service_desk_crud.ticket.get_full(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Chamado não encontrado")
    
    # Gerar QR Code para o chamado
    base_url = str(request.base_url).rstrip('/')
    qr_content = f"{base_url}/servicos/chamado/{ticket.id}"
    qr_img = QRService.generate_qr_code(qr_content)
    
    return templates.TemplateResponse("service_desk/detail.html", {
        "request": request,
        "user": current_user,
        "ticket": ticket,
        "qr_code": qr_img.getvalue().hex(), # Enviando como hex para simplificar (ou via endpoint)
        "statuses": ServiceStatus,
        "title": f"Chamado: {ticket.codigo}"
    })

# --- Admin Area for Categories and Definitions ---

@router.get("/admin/categorias", response_class=HTMLResponse)
async def list_categories(
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    user_role = str(current_user.role.value).lower()
    if user_role not in [UserRole.ADMIN, UserRole.GERENTE, UserRole.GERENTE_INFRA]:
        return RedirectResponse(url="/servicos", status_code=303)
    
    categories = await service_desk_crud.category.get_multi(db)
    return templates.TemplateResponse("service_desk/admin/categories.html", {
        "request": request,
        "user": current_user,
        "categories": categories,
        "title": "Gerenciar Categorias"
    })

@router.post("/chamado/{ticket_id}/update")
async def update_ticket_status(
    ticket_id: int,
    status: Annotated[str, Form()],
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Atualiza o status de um chamado (Admin/Técnico)"""
    user_role = str(current_user.role.value).lower()
    if user_role not in [UserRole.ADMIN, UserRole.GERENTE, UserRole.TECNICO, UserRole.GERENTE_INFRA]:
        raise HTTPException(status_code=403)
        
    ticket = await service_desk_crud.ticket.get(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404)
        
    ticket.status = ServiceStatus(status)
    if ticket.status == ServiceStatus.RESOLVIDO:
        ticket.data_fechamento = datetime.now()
        
    if not ticket.tecnico_id:
        ticket.tecnico_id = current_user.id
        
    await db.commit()
    return RedirectResponse(url=f"/servicos/chamado/{ticket.id}", status_code=303)

@router.post("/admin/categorias")
async def create_category(
    nome: Annotated[str, Form()],
    setor: Annotated[str, Form()],
    descricao: Annotated[Optional[str], Form()] = None,
    current_user: Annotated[User, Depends(get_active_user_web)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
):
    user_role = str(current_user.role.value).lower()
    if user_role not in [UserRole.ADMIN, UserRole.GERENTE, UserRole.GERENTE_INFRA]:
        raise HTTPException(status_code=403)
    
    cat_in = ServiceCategoryCreate(nome=nome, setor=setor, descricao=descricao)
    await service_desk_crud.category.create(db, obj_in=cat_in)
    return RedirectResponse(url="/servicos/admin/categorias", status_code=303)
