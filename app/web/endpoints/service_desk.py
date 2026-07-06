# app/web/endpoints/service_desk.py
import os
import shutil
from typing import Annotated, Optional
from datetime import datetime
from fastapi import APIRouter, Request, Depends, Form, HTTPException, UploadFile, File
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
from app.core.datetime_utils import now_sp

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
    if current_user.role not in [UserRole.ADMIN, UserRole.GERENTE, UserRole.TECNICO, UserRole.GERENTE_INFRA]:
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
    
    if current_user.role in [UserRole.ADMIN, UserRole.GERENTE, UserRole.TECNICO, UserRole.GERENTE_INFRA]:
        stats = {
            "abertos": await db.scalar(select(func.count(ServiceTicket.id)).filter(ServiceTicket.status == ServiceStatus.ABERTO)),
            "em_atendimento": await db.scalar(select(func.count(ServiceTicket.id)).filter(ServiceTicket.status == ServiceStatus.EM_ATENDIMENTO)),
            "resolvidos": await db.scalar(select(func.count(ServiceTicket.id)).filter(ServiceTicket.status == ServiceStatus.RESOLVIDO))
        }
    else:
        stats = None

    dashboard_data = None
    if current_user.role in [UserRole.ADMIN, UserRole.GERENTE, UserRole.GERENTE_INFRA]:
        # Tickets by status
        status_counts = await db.execute(
            select(ServiceTicket.status, func.count(ServiceTicket.id))
            .group_by(ServiceTicket.status)
        )
        status_data = {}
        for row in status_counts.all():
            if row[0]:
                val = row[0].value if hasattr(row[0], 'value') else row[0]
                status_data[str(val)] = row[1]

        # Tickets by priority
        priority_counts = await db.execute(
            select(ServiceTicket.prioridade, func.count(ServiceTicket.id))
            .group_by(ServiceTicket.prioridade)
        )
        priority_data = {}
        for row in priority_counts.all():
            if row[0]:
                val = row[0].value if hasattr(row[0], 'value') else row[0]
                priority_data[str(val)] = row[1]

        # Tickets by category
        category_counts = await db.execute(
            select(ServiceCategory.nome, func.count(ServiceTicket.id))
            .join(ServiceDefinition, ServiceDefinition.categoria_id == ServiceCategory.id)
            .join(ServiceTicket, ServiceTicket.servico_id == ServiceDefinition.id)
            .group_by(ServiceCategory.nome)
        )
        category_data = {row[0]: row[1] for row in category_counts.all()}

        # Top users (solicitantes)
        user_counts = await db.execute(
            select(User.nome, func.count(ServiceTicket.id))
            .join(ServiceTicket, ServiceTicket.solicitante_id == User.id)
            .group_by(User.nome)
            .order_by(func.count(ServiceTicket.id).desc())
            .limit(5)
        )
        user_data = {row[0]: row[1] for row in user_counts.all()}

        dashboard_data = {
            "status": status_data,
            "priority": priority_data,
            "category": category_data,
            "users": user_data
        }

    categories = await service_desk_crud.category.get_multi(db)

    return templates.TemplateResponse("service_desk/list.html", {
        "request": request,
        "user": current_user,
        "tickets": tickets,
        "stats": stats,
        "dashboard_data": dashboard_data,
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
    db: Annotated[AsyncSession, Depends(get_db)],
    foto: Annotated[Optional[UploadFile], File()] = None
):
    foto_path = None
    if foto and foto.filename:
        upload_dir = "static/uploads/tickets"
        os.makedirs(upload_dir, exist_ok=True)
        unique_filename = f"{int(now_sp().timestamp())}_{foto.filename}"
        file_path = os.path.join(upload_dir, unique_filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(foto.file, buffer)
        foto_path = f"/{file_path}"

    ticket_in = ServiceTicketCreate(
        titulo=titulo,
        servico_id=servico_id,
        prioridade=ServicePriority(prioridade),
        descricao=descricao,
        foto=foto_path
    )
    ticket = await service_desk_crud.ticket.create_with_codigo(db, obj_in=ticket_in, solicitante_id=current_user.id)
    return RedirectResponse(url=f"/servicos/chamado/{ticket.codigo}", status_code=303)

@router.get("/chamado/{ticket_id}", response_class=HTMLResponse)
async def ticket_detail(
    request: Request,
    ticket_id: str,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)],
    error: Optional[str] = None,
    success: Optional[str] = None
):
    ticket = await service_desk_crud.ticket.get_full(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Chamado não encontrado")
    
    # Gerar QR Code para o chamado (baseado no código CH-YYYY-NNNN)
    base_url = str(request.base_url).rstrip('/')
    qr_content = f"{base_url}/servicos/chamado/{ticket.codigo}"
    qr_base64 = QRService.generate_qr_base64(qr_content)
    
    # Fetch stock information for technicians/admins
    stocks = []
    consumed_items = []
    user_role = str(current_user.role.value).lower()
    if user_role in ['admin', 'gerente_ti', 'gerente_infra', 'tecnico']:
        from app.models.procurement import MaterialStock, MaterialStockTransaction
        stocks = (await db.execute(
            select(MaterialStock)
            .options(selectinload(MaterialStock.product))
            .filter(MaterialStock.quantidade_saldo > 0)
        )).scalars().all()
        
        consumed_items = (await db.execute(
            select(MaterialStockTransaction)
            .options(selectinload(MaterialStockTransaction.product))
            .filter(
                MaterialStockTransaction.origem_tabela == "service_tickets",
                MaterialStockTransaction.origem_id == ticket.id
            )
        )).scalars().all()
        
    return templates.TemplateResponse("service_desk/detail.html", {
        "request": request,
        "user": current_user,
        "ticket": ticket,
        "qr_code": qr_base64,
        "statuses": ServiceStatus,
        "title": f"Chamado: {ticket.codigo}",
        "stocks": stocks,
        "consumed_items": consumed_items,
        "error": error,
        "success": success
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

@router.post("/chamado/{ticket_id}/consumir-estoque")
async def ticket_consume_stock(
    ticket_id: str,
    product_id: Annotated[int, Form()],
    quantidade: Annotated[float, Form()],
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    user_role = str(current_user.role.value).lower()
    if user_role not in [UserRole.ADMIN, UserRole.GERENTE, UserRole.TECNICO, UserRole.GERENTE_INFRA]:
        raise HTTPException(status_code=403, detail="Não autorizado")
        
    ticket = await service_desk_crud.ticket.get_full(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Chamado não encontrado")
        
    from decimal import Decimal
    qty_decimal = Decimal(str(quantidade))
    from app.crud.procurement import create_or_update_stock, get_material_stock
    stock = await get_material_stock(db, product_id)
    if not stock or stock.quantidade_saldo < qty_decimal:
        return RedirectResponse(url=f"/servicos/chamado/{ticket.codigo}?error=Saldo+insuficiente+no+estoque!", status_code=303)
        
    # Consume item
    justificativa = f"Consumo lançado para o chamado {ticket.codigo}"
    await create_or_update_stock(
        db=db,
        product_id=product_id,
        quantidade=quantidade,
        tipo="Saída",
        user_id=current_user.id,
        justificativa=justificativa,
        origem_tabela="service_tickets",
        origem_id=ticket.id
    )
    
    # Post interaction on ticket
    product_name = stock.product.nome if stock.product else "Item"
    obj_in = ServiceTicketInteractionCreate(
        ticket_id=ticket.id,
        mensagem=f"📦 ESTOQUE CONSUMIDO: {quantidade}x {product_name} retirado(s) do estoque para resolução do chamado.",
        tipo="Comentário"
    )
    await service_desk_crud.interaction.create_with_user(db, obj_in=obj_in, usuario_id=current_user.id)
    
    # Update ticket update time
    ticket.data_atualizacao = now_sp()
    await db.commit()
    
    return RedirectResponse(url=f"/servicos/chamado/{ticket.codigo}?success=Item+retirado+do+estoque+com+sucesso!", status_code=303)


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
        ticket.data_fechamento = now_sp()
        
    if not ticket.tecnico_id:
        ticket.tecnico_id = current_user.id
        
    await db.commit()
    return RedirectResponse(url=f"/servicos/chamado/{ticket.codigo}", status_code=303)

@router.post("/chamado/{ticket_id}/interacao")
async def create_interaction(
    ticket_id: str,
    mensagem: Annotated[str, Form()],
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)],
    foto: Annotated[Optional[UploadFile], File()] = None
):
    """Adiciona um comentário/interação no chamado"""
    ticket = await service_desk_crud.ticket.get_full(db, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404)
        
    foto_path = None
    if foto and foto.filename:
        upload_dir = "static/uploads/tickets"
        os.makedirs(upload_dir, exist_ok=True)
        unique_filename = f"{int(now_sp().timestamp())}_{foto.filename}"
        file_path = os.path.join(upload_dir, unique_filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(foto.file, buffer)
        foto_path = f"/{file_path}"

    obj_in = ServiceTicketInteractionCreate(
        ticket_id=ticket.id,
        mensagem=mensagem,
        tipo="Comentário",
        foto=foto_path
    )
    await service_desk_crud.interaction.create_with_user(db, obj_in=obj_in, usuario_id=current_user.id)
    
    # Atualiza a data de atualização do chamado
    ticket.data_atualizacao = now_sp()
    await db.commit()
    
    return RedirectResponse(url=f"/servicos/chamado/{ticket.codigo}", status_code=303)

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
