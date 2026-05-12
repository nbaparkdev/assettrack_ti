# app/web/endpoints/service_desk.py
import os
from typing import Annotated, Optional
from datetime import datetime
from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.web.dependencies import get_active_user_web
from app.models.user import User, UserRole
from app.models.service_desk import ServiceCategory, ServiceDefinition, ServiceTicket, ServiceStatus, ServicePriority
from app.database import get_db
from app.crud import service_desk as service_desk_crud
from app.schemas.service_desk import (
    ServiceTicketCreate, ServiceCategoryCreate, 
    ServiceDefinitionCreate, ServiceTicketInteractionCreate
)
from app.services.qr_service import QRService

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def service_desk_home(
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)],
    query: Optional[str] = None,
    status: Optional[str] = None,
    prioridade: Optional[str] = None,
    categoria_id: Optional[str] = None,
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None
):
    """Página principal do Service Desk - Lista de chamados do usuário ou todos para admin/técnico"""
    user_role = str(current_user.role.value).lower()
    
    # Process dates if provided
    dt_inicio = None
    dt_fim = None
    if data_inicio:
        try:
            dt_inicio = datetime.strptime(data_inicio, "%Y-%m-%d")
        except ValueError:
            pass
    if data_fim:
        try:
            dt_fim = datetime.strptime(data_fim, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
        except ValueError:
            pass
            
    # Process categoria_id
    cat_id = None
    if categoria_id and categoria_id.isdigit():
        cat_id = int(categoria_id)
            
    # Determine scope
    solicitante_id = None
    if user_role not in [UserRole.ADMIN, UserRole.GERENTE, UserRole.TECNICO, UserRole.GERENTE_INFRA]:
        solicitante_id = current_user.id
        
    tickets = await service_desk_crud.ticket.search_tickets(
        db, 
        query=query, 
        status=ServiceStatus(status) if status else None,
        prioridade=ServicePriority(prioridade) if prioridade else None,
        categoria_id=cat_id,
        solicitante_id=solicitante_id,
        data_inicio=dt_inicio,
        data_fim=dt_fim
    )
    
    if user_role in [UserRole.ADMIN, UserRole.GERENTE, UserRole.TECNICO, UserRole.GERENTE_INFRA]:
        stats = {
            "abertos": await db.scalar(select(func.count(ServiceTicket.id)).filter(ServiceTicket.status == ServiceStatus.ABERTO)),
            "em_atendimento": await db.scalar(select(func.count(ServiceTicket.id)).filter(ServiceTicket.status == ServiceStatus.EM_ATENDIMENTO)),
            "resolvidos": await db.scalar(select(func.count(ServiceTicket.id)).filter(ServiceTicket.status == ServiceStatus.RESOLVIDO))
        }
    else:
        stats = None

    categories = await service_desk_crud.category.get_multi(db)

    return templates.TemplateResponse("service_desk/list.html", {
        "request": request,
        "user": current_user,
        "tickets": tickets,
        "stats": stats,
        "title": "Service Desk",
        "categories": categories,
        "filters": {
            "query": query or "",
            "status": status or "",
            "prioridade": prioridade or "",
            "categoria_id": categoria_id or "",
            "data_inicio": data_inicio or "",
            "data_fim": data_fim or ""
        },
        "statuses": [s.value for s in ServiceStatus],
        "priorities": [p.value for p in ServicePriority]
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
    ticket_id: str,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    ticket = await service_desk_crud.ticket.get_full(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Chamado não encontrado")
    
    # Gerar QR Code para o chamado (baseado no código CH-YYYY-NNNN)
    base_url = str(request.base_url).rstrip('/')
    qr_content = f"{base_url}/servicos/chamado/{ticket.codigo}"
    qr_base64 = QRService.generate_qr_base64(qr_content)
    
    return templates.TemplateResponse("service_desk/detail.html", {
        "request": request,
        "user": current_user,
        "ticket": ticket,
        "qr_code": qr_base64,
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
    ticket_id: str,
    status: Annotated[str, Form()],
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Atualiza o status de um chamado (Admin/Técnico)"""
    user_role = str(current_user.role.value).lower()
    if user_role not in [UserRole.ADMIN, UserRole.GERENTE, UserRole.TECNICO, UserRole.GERENTE_INFRA]:
        raise HTTPException(status_code=403)
        
    ticket = await service_desk_crud.ticket.get_full(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404)
        
    ticket.status = ServiceStatus(status)
    if ticket.status == ServiceStatus.RESOLVIDO:
        ticket.data_fechamento = datetime.now()
        
    if not ticket.tecnico_id:
        ticket.tecnico_id = current_user.id
        
    await db.commit()
    return RedirectResponse(url=f"/servicos/chamado/{ticket.id}", status_code=303)

@router.post("/chamado/{ticket_id}/interacao")
async def create_interaction(
    ticket_id: str,
    mensagem: Annotated[str, Form()],
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Adiciona um comentário/interação no chamado"""
    ticket = await service_desk_crud.ticket.get_full(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404)
        
    obj_in = ServiceTicketInteractionCreate(
        ticket_id=ticket.id,
        mensagem=mensagem,
        tipo="Comentário"
    )
    await service_desk_crud.interaction.create_with_user(db, obj_in=obj_in, usuario_id=current_user.id)
    
    # Atualiza a data de atualização do chamado
    ticket.data_atualizacao = datetime.now()
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

@router.get("/admin/servicos", response_class=HTMLResponse)
async def list_services(
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    user_role = str(current_user.role.value).lower()
    if user_role not in [UserRole.ADMIN, UserRole.GERENTE, UserRole.GERENTE_INFRA]:
        return RedirectResponse(url="/servicos", status_code=303)
    
    # Busca todas as definições com suas categorias para exibir na tabela
    stmt = select(ServiceDefinition).options(selectinload(ServiceDefinition.categoria))
    result = await db.execute(stmt)
    services = result.scalars().all()
    
    categories = await service_desk_crud.category.get_multi(db)
    return templates.TemplateResponse("service_desk/admin/services.html", {
        "request": request,
        "user": current_user,
        "services": services,
        "categories": categories,
        "priorities": ServicePriority,
        "title": "Gerenciar Serviços"
    })

@router.post("/admin/servicos")
async def create_service_definition(
    categoria_id: Annotated[int, Form()],
    nome: Annotated[str, Form()],
    prioridade_padrao: Annotated[str, Form()],
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)],
    descricao: Annotated[Optional[str], Form()] = None,
    tempo_estimado_horas: Annotated[Optional[float], Form()] = None
):
    user_role = str(current_user.role.value).lower()
    if user_role not in [UserRole.ADMIN, UserRole.GERENTE, UserRole.GERENTE_INFRA]:
        raise HTTPException(status_code=403)
    
    def_in = ServiceDefinitionCreate(
        categoria_id=categoria_id,
        nome=nome,
        prioridade_padrao=ServicePriority(prioridade_padrao),
        descricao=descricao,
        tempo_estimado_horas=tempo_estimado_horas
    )
    await service_desk_crud.definition.create(db, obj_in=def_in)
    return RedirectResponse(url="/servicos/admin/servicos", status_code=303)
