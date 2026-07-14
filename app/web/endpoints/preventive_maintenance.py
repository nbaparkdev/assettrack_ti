# app/web/endpoints/preventive_maintenance.py
import os
from typing import Annotated, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Request, Depends, HTTPException, Form, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.web.dependencies import get_active_user_web, check_preventive_maintenance_enabled
from app.models.user import User, UserRole
from app.models.preventive_maintenance import (
    MaintenancePlan, MaintenanceOrder, MaintenanceType, OrderStatus,
    MaintenancePriority, MaintenanceCriticality, MaintenanceChecklist
)
from app.models.asset import Asset
from app.database import get_db
from app.crud import preventive_maintenance as pm_crud
from app.core.datetime_utils import now_sp

router = APIRouter(dependencies=[Depends(check_preventive_maintenance_enabled)])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def pm_dashboard(
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Dashboard principal do módulo de Manutenção Preventiva"""
    
    # Estatísticas básicas
    stats = {
        "vencidas": 0,
        "hoje": 0,
        "semana": 0,
        "concluidas": 0,
        "em_andamento": 0,
        "equipamentos_indisponiveis": 0
    }
    
    # Obter todas as ordens para calcular estatísticas
    ordens = await pm_crud.maintenance_order.get_multi(db, limit=1000)
    
    now = now_sp()
    today = now.date()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=7)
    
    for ordem in ordens:
        if ordem.status == OrderStatus.CONCLUIDA:
            stats["concluidas"] += 1
        elif ordem.status == OrderStatus.EM_ANDAMENTO:
            stats["em_andamento"] += 1
        
        # Verificar vencidas, hoje e semana
        if ordem.data_agendada:
            if ordem.data_agendada.date() < today and ordem.status not in [OrderStatus.CONCLUIDA, OrderStatus.CANCELADA]:
                stats["vencidas"] += 1
            if ordem.data_agendada.date() == today:
                stats["hoje"] += 1
            if week_start <= ordem.data_agendada.date() < week_end:
                stats["semana"] += 1
    
    # Equipamentos indisponíveis (status = Manutenção)
    from app.models.asset import AssetStatus
    stats["equipamentos_indisponiveis"] = await db.scalar(
        select(func.count(Asset.id)).filter(Asset.status == AssetStatus.MANUTENCAO)
    )
    
    # Dados para gráficos
    dashboard_data = None
    if current_user.role in [UserRole.ADMIN, UserRole.GERENTE, UserRole.GERENTE_INFRA, UserRole.TECNICO]:
        # Ordens por tipo
        tipo_counts = await db.execute(
            select(MaintenanceOrder.tipo, func.count(MaintenanceOrder.id))
            .group_by(MaintenanceOrder.tipo)
        )
        tipo_data = {}
        for row in tipo_counts.all():
            if row[0]:
                val = row[0].value if hasattr(row[0], 'value') else row[0]
                tipo_data[str(val)] = row[1]
        
        # Ordens por status
        status_counts = await db.execute(
            select(MaintenanceOrder.status, func.count(MaintenanceOrder.id))
            .group_by(MaintenanceOrder.status)
        )
        status_data = {}
        for row in status_counts.all():
            if row[0]:
                val = row[0].value if hasattr(row[0], 'value') else row[0]
                status_data[str(val)] = row[1]
        
        # Ordens por técnico
        tecnico_counts = await db.execute(
            select(User.nome, func.count(MaintenanceOrder.id))
            .join(MaintenanceOrder, MaintenanceOrder.tecnico_id == User.id)
            .group_by(User.nome)
            .order_by(func.count(MaintenanceOrder.id).desc())
            .limit(5)
        )
        tecnico_data = {row[0]: row[1] for row in tecnico_counts.all()}
        
        dashboard_data = {
            "tipo": tipo_data,
            "status": status_data,
            "tecnicos": tecnico_data
        }
    
    # Próximas ordens (próximas 10 ordens)
    proximas_ordens = []
    stmt = (
        select(MaintenanceOrder)
        .options(
            selectinload(MaintenanceOrder.asset).selectinload(Asset.current_local),
            selectinload(MaintenanceOrder.asset).selectinload(Asset.current_departamento),
            selectinload(MaintenanceOrder.tecnico)
        )
        .filter(MaintenanceOrder.status.not_in([OrderStatus.CONCLUIDA, OrderStatus.CANCELADA]))
        .order_by(MaintenanceOrder.data_agendada)
        .limit(10)
    )
    result = await db.execute(stmt)
    proximas_ordens = result.scalars().all()
    
    return templates.TemplateResponse("preventive_maintenance/dashboard.html", {
        "request": request,
        "user": current_user,
        "stats": stats,
        "dashboard_data": dashboard_data,
        "proximas_ordens": proximas_ordens,
        "title": "Manutenção Preventiva"
    })


@router.get("/planos", response_class=HTMLResponse)
async def list_plans(
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)],
    tipo: Optional[str] = None,
    ativo: Optional[str] = None,
    criticidade: Optional[str] = None
):
    """Lista de planos de manutenção"""
    
    planos = await pm_crud.maintenance_plan.get_multi(db)
    
    # Filtrar resultados se necessário
    filtered_planos = []
    for plano in planos:
        match = True
        if tipo and plano.tipo.value != tipo:
            match = False
        if ativo is not None:
            is_active = str(plano.ativo).lower() == ativo.lower()
            if not is_active:
                match = False
        if criticidade and plano.criticidade.value != criticidade:
            match = False
        if match:
            filtered_planos.append(plano)
    
    return templates.TemplateResponse("preventive_maintenance/plans_list.html", {
        "request": request,
        "user": current_user,
        "planos": filtered_planos,
        "filters": {
            "tipo": tipo or "",
            "ativo": ativo or "",
            "criticidade": criticidade or ""
        },
        "title": "Planos de Manutenção"
    })


@router.get("/ordens", response_class=HTMLResponse)
async def list_orders(
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)],
    status: Optional[str] = None,
    tipo: Optional[str] = None,
    prioridade: Optional[str] = None,
    tecnico_id: Optional[str] = None
):
    """Lista de ordens de serviço de manutenção"""
    
    # Obter técnicos para filtro
    stmt = select(User).filter(User.role.in_([UserRole.ADMIN, UserRole.GERENTE, UserRole.TECNICO, UserRole.GERENTE_INFRA]))
    result = await db.execute(stmt)
    tecnicos = result.scalars().all()
    
    # Construir query com filtros
    stmt = select(MaintenanceOrder).options(
        selectinload(MaintenanceOrder.asset),
        selectinload(MaintenanceOrder.tecnico)
    )
    
    if status:
        try:
            stmt = stmt.filter(MaintenanceOrder.status == OrderStatus(status))
        except ValueError:
            pass
    
    if tipo:
        try:
            stmt = stmt.filter(MaintenanceOrder.tipo == MaintenanceType(tipo))
        except ValueError:
            pass
    
    if prioridade:
        try:
            stmt = stmt.filter(MaintenanceOrder.prioridade == MaintenancePriority(prioridade))
        except ValueError:
            pass
    
    if tecnico_id and tecnico_id.isdigit():
        stmt = stmt.filter(MaintenanceOrder.tecnico_id == int(tecnico_id))
    
    stmt = stmt.order_by(MaintenanceOrder.data_abertura.desc())
    
    result = await db.execute(stmt)
    ordens = result.scalars().all()
    
    return templates.TemplateResponse("preventive_maintenance/orders_list.html", {
        "request": request,
        "user": current_user,
        "ordens": ordens,
        "tecnicos": tecnicos,
        "filters": {
            "status": status or "",
            "tipo": tipo or "",
            "prioridade": prioridade or "",
            "tecnico_id": tecnico_id or ""
        },
        "title": "Ordens de Serviço"
    })


@router.get("/calendario", response_class=HTMLResponse)
async def maintenance_calendar(
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Calendário de manutenções"""
    import json
    
    # 1. Buscar todas as ordens de serviço
    orders_stmt = (
        select(MaintenanceOrder)
        .options(selectinload(MaintenanceOrder.asset))
    )
    orders_res = await db.execute(orders_stmt)
    orders = orders_res.scalars().all()
    
    # 2. Buscar planos ativos para exibir previsões de próxima execução
    plans_stmt = (
        select(MaintenancePlan)
        .filter(MaintenancePlan.ativo == True)
    )
    plans_res = await db.execute(plans_stmt)
    plans = plans_res.scalars().all()
    
    # 3. Formatar eventos para o FullCalendar
    calendar_events = []
    
    # Adicionar ordens de serviço
    for order in orders:
        # Definir a data do evento (priorizar agendada, senão abertura)
        event_date = order.data_agendada or order.data_abertura
        if not event_date:
            continue
            
        # Definir a cor baseada no status (evitando roxo/violeta devido ao Purple Ban)
        # Usando azul, verde, laranja, cinza, vermelho e amarelo.
        status_colors = {
            OrderStatus.ABERTA: "#2563eb",         # Blue 600
            OrderStatus.AGENDADA: "#0891b2",       # Cyan 600
            OrderStatus.EM_ANDAMENTO: "#eab308",  # Yellow 500
            OrderStatus.PAUSADA: "#4b5563",       # Gray 600
            OrderStatus.AGUARDANDO_PECA: "#f97316",# Orange 500
            OrderStatus.CONCLUIDA: "#16a34a",     # Green 600
            OrderStatus.CANCELADA: "#dc2626"      # Red 600
        }
        color = status_colors.get(order.status, "#4b5563")
        
        asset_name = order.asset.nome if order.asset else "Sem Ativo"
        calendar_events.append({
            "id": f"os-{order.id}",
            "title": f"{order.numero} - {asset_name}",
            "start": event_date.strftime("%Y-%m-%dT%H:%M:%S"),
            "url": f"/manutencao-preventiva/ordens/{order.id}",
            "backgroundColor": color,
            "borderColor": color,
            "textColor": "#ffffff" if order.status != OrderStatus.EM_ANDAMENTO else "#000000",
            "extendedProps": {
                "tipo": "Ordem de Serviço",
                "status": order.status.value,
                "numero": order.numero
            }
        })
        
    # Adicionar previsões de planos
    for plan in plans:
        if not plan.proxima_execucao:
            continue
            
        calendar_events.append({
            "id": f"plan-{plan.id}",
            "title": f"🛠️ Previsão: {plan.codigo} - {plan.nome}",
            "start": plan.proxima_execucao.strftime("%Y-%m-%d"),
            "url": f"/manutencao-preventiva/planos/{plan.id}",
            "backgroundColor": "#0f172a", # Slate 900 (Dark grey/black)
            "borderColor": "#0f172a",
            "textColor": "#ffffff",
            "extendedProps": {
                "tipo": "Previsão de Plano",
                "status": "Agendado",
                "numero": plan.codigo
            }
        })
        
    events_json = json.dumps(calendar_events)
    
    return templates.TemplateResponse("preventive_maintenance/calendar.html", {
        "request": request,
        "user": current_user,
        "events_json": events_json,
        "title": "Calendário de Manutenções"
    })


@router.get("/checklists", response_class=HTMLResponse)
async def checklists_page(
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)],
    plan_id: Optional[int] = None,
):
    """Gerenciamento global de checklists de manutenção"""
    from app.models.preventive_maintenance import MaintenanceChecklistItem

    # Buscar todos os planos para o filtro
    plans_res = await db.execute(select(MaintenancePlan).order_by(MaintenancePlan.codigo))
    all_plans = plans_res.scalars().all()

    # Buscar checklists (com filtro por plano se solicitado)
    stmt = (
        select(MaintenanceChecklist)
        .options(
            selectinload(MaintenanceChecklist.plan),
            selectinload(MaintenanceChecklist.items)
        )
        .join(MaintenancePlan, MaintenanceChecklist.plan_id == MaintenancePlan.id)
        .order_by(MaintenancePlan.codigo, MaintenanceChecklist.ordem)
    )
    if plan_id:
        stmt = stmt.filter(MaintenanceChecklist.plan_id == plan_id)

    result = await db.execute(stmt)
    checklists = result.scalars().all()

    # Totais
    total_items = sum(len(cl.items) for cl in checklists)
    total_obrigatorios = sum(
        sum(1 for it in cl.items if it.obrigatorio) for cl in checklists
    )

    return templates.TemplateResponse("preventive_maintenance/checklists.html", {
        "request": request,
        "user": current_user,
        "checklists": checklists,
        "all_plans": all_plans,
        "plan_id_filter": plan_id,
        "total_items": total_items,
        "total_obrigatorios": total_obrigatorios,
        "title": "Checklists de Manutenção"
    })


@router.get("/relatorios", response_class=HTMLResponse)
async def reports_page(
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)],
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None
):
    """Página de relatórios estatísticos e gerenciais de manutenção"""
    from datetime import datetime, timedelta
    from sqlalchemy import desc

    # Datas padrão (últimos 30 dias se não especificado)
    if data_inicio:
        dt_inicio = datetime.fromisoformat(data_inicio)
    else:
        dt_inicio = now_sp() - timedelta(days=30)
        dt_inicio = dt_inicio.replace(hour=0, minute=0, second=0, microsecond=0)
        
    if data_fim:
        dt_fim = datetime.fromisoformat(data_fim)
        dt_fim = dt_fim.replace(hour=23, minute=59, second=59, microsecond=999999)
    else:
        dt_fim = now_sp()
        dt_fim = dt_fim.replace(hour=23, minute=59, second=59, microsecond=999999)

    # 1. Estatísticas gerais de ordens concluídas
    stmt_geral = (
        select(
            func.count(MaintenanceOrder.id).label("total_concluidas"),
            func.sum(MaintenanceOrder.custo_total).label("custo_total"),
            func.avg(MaintenanceOrder.tempo_total_minutos).label("tempo_medio_minutos")
        )
        .filter(MaintenanceOrder.status == OrderStatus.CONCLUIDA)
        .filter(MaintenanceOrder.data_conclusao >= dt_inicio)
        .filter(MaintenanceOrder.data_conclusao <= dt_fim)
    )
    res_geral = await db.execute(stmt_geral)
    row_geral = res_geral.fetchone()
    
    total_concluidas = row_geral.total_concluidas or 0
    custo_total = float(row_geral.custo_total or 0.0)
    tempo_medio_minutos = float(row_geral.tempo_medio_minutos or 0.0)

    # 2. Custo total com Materiais no período
    from app.models.preventive_maintenance import MaintenanceMaterial
    stmt_materials = (
        select(func.sum(MaintenanceMaterial.valor_total))
        .join(MaintenanceOrder, MaintenanceMaterial.order_id == MaintenanceOrder.id)
        .filter(MaintenanceOrder.status == OrderStatus.CONCLUIDA)
        .filter(MaintenanceOrder.data_conclusao >= dt_inicio)
        .filter(MaintenanceOrder.data_conclusao <= dt_fim)
    )
    res_mats = await db.execute(stmt_materials)
    custo_materiais = float(res_mats.scalar() or 0.0)
    custo_mao_de_obra = max(0.0, custo_total - custo_materiais)

    # 3. Manutenções por Tipo (Distribuição)
    stmt_tipos = (
        select(
            MaintenanceOrder.tipo,
            func.count(MaintenanceOrder.id).label("quantidade"),
            func.sum(MaintenanceOrder.custo_total).label("custo")
        )
        .filter(MaintenanceOrder.status == OrderStatus.CONCLUIDA)
        .filter(MaintenanceOrder.data_conclusao >= dt_inicio)
        .filter(MaintenanceOrder.data_conclusao <= dt_fim)
        .group_by(MaintenanceOrder.tipo)
    )
    res_tipos = await db.execute(stmt_tipos)
    tipos_stats = [{"tipo": r[0].value, "quantidade": r[1], "custo": float(r[2] or 0.0)} for r in res_tipos.fetchall()]

    # 4. Desempenho dos Técnicos
    stmt_tecnicos = (
        select(
            User.nome,
            func.count(MaintenanceOrder.id).label("quantidade"),
            func.avg(MaintenanceOrder.tempo_total_minutos).label("tempo_medio")
        )
        .join(MaintenanceOrder, MaintenanceOrder.tecnico_id == User.id)
        .filter(MaintenanceOrder.status == OrderStatus.CONCLUIDA)
        .filter(MaintenanceOrder.data_conclusao >= dt_inicio)
        .filter(MaintenanceOrder.data_conclusao <= dt_fim)
        .group_by(User.nome)
    )
    res_tecnicos = await db.execute(stmt_tecnicos)
    tecnicos_stats = [{"nome": r[0], "quantidade": r[1], "tempo_medio": float(r[2] or 0.0)} for r in res_tecnicos.fetchall()]

    # 5. Equipamentos com mais manutenções (Ativos Problemáticos)
    stmt_ativos = (
        select(
            Asset.e_patrimonio,
            Asset.nome,
            func.count(MaintenanceOrder.id).label("quantidade"),
            func.sum(MaintenanceOrder.custo_total).label("custo")
        )
        .join(MaintenanceOrder, MaintenanceOrder.asset_id == Asset.id)
        .filter(MaintenanceOrder.status == OrderStatus.CONCLUIDA)
        .filter(MaintenanceOrder.data_conclusao >= dt_inicio)
        .filter(MaintenanceOrder.data_conclusao <= dt_fim)
        .group_by(Asset.e_patrimonio, Asset.nome)
        .order_by(desc("quantidade"))
        .limit(5)
    )
    res_ativos = await db.execute(stmt_ativos)
    ativos_stats = [{"patrimonio": r[0], "nome": r[1], "quantidade": r[2], "custo": float(r[3] or 0.0)} for r in res_ativos.fetchall()]

    return templates.TemplateResponse("preventive_maintenance/reports.html", {
        "request": request,
        "user": current_user,
        "data_inicio": dt_inicio.strftime('%Y-%m-%d'),
        "data_fim": dt_fim.strftime('%Y-%m-%d'),
        "total_concluidas": total_concluidas,
        "custo_total": custo_total,
        "custo_materiais": custo_materiais,
        "custo_materials": custo_materiais, # Fallback de segurança para o template
        "custo_mao_de_obra": custo_mao_de_obra,
        "tempo_medio_minutos": tempo_medio_minutos,
        "tipos_stats": tipos_stats,
        "tecnicos_stats": tecnicos_stats,
        "ativos_stats": ativos_stats,
        "title": "Relatórios de Manutenção"
    })


@router.get("/ordens/nova", response_class=HTMLResponse)
async def new_order_form(
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Formulário para criação de nova ordem de manutenção"""
    # Obter ativos
    assets = await db.execute(select(Asset))
    assets = assets.scalars().all()
    
    # Obter técnicos
    technicians = await db.execute(select(User).filter(User.role.in_([
        UserRole.ADMIN, UserRole.GERENTE, UserRole.TECNICO, UserRole.GERENTE_INFRA
    ])))
    technicians = technicians.scalars().all()
    
    # Obter planos de manutenção ativos
    plans = await db.execute(select(MaintenancePlan).filter(MaintenancePlan.ativo == True))
    plans = plans.scalars().all()
    
    return templates.TemplateResponse("preventive_maintenance/order_form.html", {
        "request": request,
        "user": current_user,
        "assets": assets,
        "technicians": technicians,
        "plans": plans,
        "maintenance_types": [mt.value for mt in MaintenanceType],
        "maintenance_priorities": [mp.value for mp in MaintenancePriority],
        "title": "Nova Ordem de Serviço"
    })

@router.post("/ordens/nova")
async def create_order(
    request: Request,
    tipo: Annotated[str, Form()],
    prioridade: Annotated[str, Form()],
    descricao: Annotated[str, Form()],
    asset_id: Annotated[Optional[str], Form()] = None,
    infra_predial_servico: Annotated[Optional[str], Form()] = None,
    plan_id: Annotated[Optional[str], Form()] = None,
    tecnico_id: Annotated[Optional[str], Form()] = None,
    data_agendada: Annotated[Optional[str], Form()] = None,
    current_user: Annotated[User, Depends(get_active_user_web)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
):
    """Cria uma nova ordem de manutenção"""
    from app.models.preventive_maintenance import MaintenanceOrder
    from sqlalchemy import func
    
    # Gerar o número da ordem
    now = now_sp()
    year = now.year
    result = await db.execute(
        select(func.count(MaintenanceOrder.id))
        .filter(func.extract('year', MaintenanceOrder.data_abertura) == year)
    )
    count = result.scalar() or 0
    numero = f"OS-{year}-{count + 1:05d}"
    
    parsed_asset_id = None
    if asset_id and asset_id.strip() and asset_id.strip() != "None" and asset_id.strip().isdigit():
        parsed_asset_id = int(asset_id)
        
    # Criar a ordem diretamente usando o model
    order = MaintenanceOrder(
        numero=numero,
        asset_id=parsed_asset_id,
        infra_predial_servico=infra_predial_servico if not parsed_asset_id else None,
        tipo=MaintenanceType(tipo),
        prioridade=MaintenancePriority(prioridade),
        observacoes=descricao,
        status=OrderStatus.ABERTA,
        data_abertura=now_sp()
    )
    
    # Converter plan_id para int se não for vazio
    if plan_id and plan_id.strip():
        order.plan_id = int(plan_id)
    
    # Converter tecnico_id para int se não for vazio
    if tecnico_id and tecnico_id.strip():
        order.tecnico_id = int(tecnico_id)
    
    if data_agendada:
        order.data_agendada = datetime.fromisoformat(data_agendada)
    
    db.add(order)
    await db.commit()
    await db.refresh(order)

    # Disparar notificação se houver técnico associado
    if order.tecnico_id:
        try:
            from app.models.user import User
            from app.models.asset import Asset
            from app.services.notification_service import notification_service
            
            tech_res = await db.execute(select(User).filter(User.id == order.tecnico_id))
            tech = tech_res.scalar_one_or_none()
            
            asset_name = order.infra_predial_servico or "Manutenção de Infra Predial"
            if order.asset_id:
                asset_res = await db.execute(select(Asset).filter(Asset.id == order.asset_id))
                asset = asset_res.scalar_one_or_none()
                if asset:
                    asset_name = asset.nome
            
            if tech:
                await notification_service.notify_order_assigned(
                    db=db,
                    order_id=order.id,
                    order_code=order.numero,
                    technician_id=tech.id,
                    technician_email=tech.email,
                    asset_name=asset_name,
                    priority=order.prioridade.value,
                    data_agendada=order.data_agendada
                )
                await db.commit()
        except Exception as e:
            print(f"[NOTIFICATION ERROR] Falha ao notificar técnico na criação da OS: {e}")
    
    return RedirectResponse(url=f"/manutencao-preventiva/ordens/{order.id}", status_code=303)



@router.get("/ordens/{order_id}", response_class=HTMLResponse)
async def order_detail(
    request: Request,
    order_id: int,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)],
    error: Optional[str] = None
):
    """Página de detalhes da ordem de manutenção"""
    from app.models.preventive_maintenance import MaintenanceExecution, MaintenanceHistory
    from app.models.procurement import MaterialStock

    # Obter ordem com todos os relacionamentos necessários
    stmt = (
        select(MaintenanceOrder)
        .options(
            selectinload(MaintenanceOrder.asset),
            selectinload(MaintenanceOrder.tecnico),
            selectinload(MaintenanceOrder.plan),
            selectinload(MaintenanceOrder.materials),
            selectinload(MaintenanceOrder.photos),
            selectinload(MaintenanceOrder.executions)
                .selectinload(MaintenanceExecution.checklist_item),
            selectinload(MaintenanceOrder.executions)
                .selectinload(MaintenanceExecution.executado_por),
            selectinload(MaintenanceOrder.history)
                .selectinload(MaintenanceHistory.usuario)
        )
        .filter(MaintenanceOrder.id == order_id)
    )
    result = await db.execute(stmt)
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Ordem de serviço não encontrada")

    # Obter checklists com items
    checklists = []
    if order.plan_id:
        from app.models.preventive_maintenance import MaintenanceChecklistItem
        stmt = (
            select(MaintenanceChecklist)
            .options(selectinload(MaintenanceChecklist.items))
            .filter(MaintenanceChecklist.plan_id == order.plan_id)
            .order_by(MaintenanceChecklist.ordem)
        )
        result = await db.execute(stmt)
        checklists = result.scalars().all()

    # Obter itens do estoque com saldo disponível
    stock_stmt = (
        select(MaterialStock)
        .options(selectinload(MaterialStock.product))
        .filter(MaterialStock.quantidade_saldo > 0)
    )
    stock_res = await db.execute(stock_stmt)
    available_stock = stock_res.scalars().all()

    return templates.TemplateResponse("preventive_maintenance/order_detail.html", {
        "request": request,
        "user": current_user,
        "order": order,
        "checklists": checklists,
        "statuses": OrderStatus,
        "title": f"Ordem de Serviço: {order.numero}",
        "error": error,
        "available_stock": available_stock
    })

# --- Endpoints para Planos de Manutenção ---

@router.get("/planos/novo", response_class=HTMLResponse)
async def new_plan_form(
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Formulário para criação de novo plano de manutenção"""
    return templates.TemplateResponse("preventive_maintenance/plan_form.html", {
        "request": request,
        "user": current_user,
        "maintenance_types": [mt.value for mt in MaintenanceType],
        "maintenance_priorities": [mp.value for mp in MaintenancePriority],
        "maintenance_criticalities": [mc.value for mc in MaintenanceCriticality],
        "title": "Novo Plano de Manutenção"
    })

@router.post("/planos/novo")
async def create_plan(
    request: Request,
    nome: Annotated[str, Form()],
    tipo: Annotated[str, Form()],
    periodicidade: Annotated[str, Form()],
    criticidade: Annotated[str, Form()],
    descricao: Annotated[str, Form()],
    current_user: Annotated[User, Depends(get_active_user_web)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
):
    """Cria um novo plano de manutenção"""
    from app.models.preventive_maintenance import MaintenancePlan
    from sqlalchemy import func
    from app.models.preventive_maintenance import MaintenancePeriodicity
    
    # Gerar o código do plano
    now = now_sp()
    year = now.year
    result = await db.execute(
        select(func.count(MaintenancePlan.id))
        .filter(func.extract('year', MaintenancePlan.data_criacao) == year)
    )
    count = result.scalar() or 0
    codigo = f"PLAN-{year}-{count + 1:05d}"
    
    # Criar o plano diretamente
    plan = MaintenancePlan(
        codigo=codigo,
        nome=nome,
        tipo=MaintenanceType(tipo),
        periodicidade=MaintenancePeriodicity.MENSAL,  # Valor padrão
        criticidade=MaintenanceCriticality(criticidade),
        descricao=descricao,
        ativo=True,
        data_criacao=now_sp(),
        proxima_execucao=now_sp()  # Valor padrão
    )
    
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    
    return RedirectResponse(url=f"/manutencao-preventiva/planos", status_code=303)


# --- Transições de Status das Ordens ---

@router.post("/ordens/{order_id}/iniciar")
async def start_order(
    order_id: int,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Iniciar uma ordem de manutenção (Aberta/Agendada → Em Andamento)"""
    from app.models.preventive_maintenance import MaintenanceHistory

    order = await pm_crud.maintenance_order.get(db, id=order_id)
    if not order or order.status not in [OrderStatus.ABERTA, OrderStatus.AGENDADA, OrderStatus.PAUSADA]:
        return RedirectResponse(url=f"/manutencao-preventiva/ordens/{order_id}", status_code=303)

    status_anterior = order.status.value
    order.status = OrderStatus.EM_ANDAMENTO
    order.data_inicio = now_sp()
    if not order.tecnico_id:
        order.tecnico_id = current_user.id
    db.add(order)

    history = MaintenanceHistory(
        order_id=order.id,
        acao="Ordem Iniciada",
        descricao=f"Ordem iniciada por {current_user.nome}",
        usuario_id=current_user.id,
        status_anterior=status_anterior,
        status_novo=OrderStatus.EM_ANDAMENTO.value
    )
    db.add(history)
    await db.commit()

    return RedirectResponse(url=f"/manutencao-preventiva/ordens/{order_id}", status_code=303)


@router.post("/ordens/{order_id}/pausar")
async def pause_order(
    order_id: int,
    motivo: Annotated[Optional[str], Form()] = None,
    current_user: Annotated[User, Depends(get_active_user_web)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
):
    """Pausar uma ordem em andamento"""
    from app.models.preventive_maintenance import MaintenanceHistory

    order = await pm_crud.maintenance_order.get(db, id=order_id)
    if not order or order.status != OrderStatus.EM_ANDAMENTO:
        return RedirectResponse(url=f"/manutencao-preventiva/ordens/{order_id}", status_code=303)

    status_anterior = order.status.value
    order.status = OrderStatus.PAUSADA
    order.data_pausa = now_sp()

    # Calcular tempo acumulado
    if order.data_inicio:
        elapsed = (now_sp() - order.data_inicio).total_seconds() / 60
        order.tempo_total_minutos = (order.tempo_total_minutos or 0) + int(elapsed)

    db.add(order)

    desc = f"Ordem pausada por {current_user.nome}"
    if motivo:
        desc += f". Motivo: {motivo}"

    history = MaintenanceHistory(
        order_id=order.id,
        acao="Ordem Pausada",
        descricao=desc,
        usuario_id=current_user.id,
        status_anterior=status_anterior,
        status_novo=OrderStatus.PAUSADA.value
    )
    db.add(history)
    await db.commit()

    return RedirectResponse(url=f"/manutencao-preventiva/ordens/{order_id}", status_code=303)


@router.post("/ordens/{order_id}/concluir")
async def complete_order(
    order_id: int,
    solucao: Annotated[Optional[str], Form()] = None,
    custo_total: Annotated[Optional[str], Form()] = None,
    current_user: Annotated[User, Depends(get_active_user_web)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
):
    """Concluir uma ordem de manutenção"""
    from app.models.preventive_maintenance import MaintenanceHistory

    order = await pm_crud.maintenance_order.get(db, id=order_id)
    if not order or order.status in [OrderStatus.CONCLUIDA, OrderStatus.CANCELADA]:
        return RedirectResponse(url=f"/manutencao-preventiva/ordens/{order_id}", status_code=303)

    status_anterior = order.status.value
    order.status = OrderStatus.CONCLUIDA
    order.data_conclusao = now_sp()
    order.solucao = solucao if solucao else None

    # Calcular tempo total
    if order.data_inicio and order.status != OrderStatus.PAUSADA:
        elapsed = (now_sp() - order.data_inicio).total_seconds() / 60
        order.tempo_total_minutos = (order.tempo_total_minutos or 0) + int(elapsed)

    # Calcular custo acumulado de materiais
    from app.models.preventive_maintenance import MaintenanceMaterial
    stmt_mats = select(func.sum(MaintenanceMaterial.valor_total)).filter(MaintenanceMaterial.order_id == order.id)
    res_mats = await db.execute(stmt_mats)
    total_materials = res_mats.scalar() or 0.0

    extra_cost = 0.0
    if custo_total and custo_total.strip():
        try:
            clean = custo_total.replace('.', '').replace(',', '.') if ',' in custo_total else custo_total
            extra_cost = float(clean)
        except ValueError:
            pass

    order.custo_total = float(total_materials) + extra_cost
    db.add(order)

    # Atualizar plano: data_ultima_execucao e proxima_execucao
    if order.plan_id:
        plan = await pm_crud.maintenance_plan.get(db, id=order.plan_id)
        if plan:
            plan.data_ultima_execucao = now_sp()
            from app.models.preventive_maintenance import MaintenancePeriodicity
            periodicity_days = {
                MaintenancePeriodicity.DIARIA: 1,
                MaintenancePeriodicity.SEMANAL: 7,
                MaintenancePeriodicity.QUINZENAL: 15,
                MaintenancePeriodicity.MENSAL: 30,
                MaintenancePeriodicity.BIMESTRAL: 60,
                MaintenancePeriodicity.TRIMESTRAL: 90,
                MaintenancePeriodicity.SEMESTRAL: 180,
                MaintenancePeriodicity.ANUAL: 365,
            }
            days = periodicity_days.get(plan.periodicidade, plan.dias_personalizado or 30)
            plan.proxima_execucao = now_sp() + timedelta(days=days)
            db.add(plan)

    history = MaintenanceHistory(
        order_id=order.id,
        acao="Ordem Concluída",
        descricao=f"Ordem concluída por {current_user.nome}" + (f". Solução: {solucao[:100]}" if solucao else ""),
        usuario_id=current_user.id,
        status_anterior=status_anterior,
        status_novo=OrderStatus.CONCLUIDA.value
    )
    db.add(history)
    await db.commit()

    # Disparar notificação de conclusão para os gestores
    try:
        from app.services.notification_service import notification_service
        from app.models.asset import Asset
        
        asset_res = await db.execute(select(Asset).filter(Asset.id == order.asset_id))
        asset = asset_res.scalar_one_or_none()
        asset_name = asset.nome if asset else "Equipamento"
        
        await notification_service.notify_order_completed(
            db=db,
            order_id=order.id,
            order_code=order.numero,
            technician_name=current_user.nome,
            asset_name=asset_name,
            custo_total=float(order.custo_total or 0)
        )
        await db.commit() # Commita a notificação criada internamente no serviço
    except Exception as e:
        print(f"[NOTIFICATION ERROR] Falha ao notificar conclusão da OS: {e}")

    return RedirectResponse(url=f"/manutencao-preventiva/ordens/{order_id}", status_code=303)


@router.post("/ordens/{order_id}/cancelar")
async def cancel_order(
    order_id: int,
    motivo: Annotated[Optional[str], Form()] = None,
    current_user: Annotated[User, Depends(get_active_user_web)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
):
    """Cancelar uma ordem de manutenção"""
    from app.models.preventive_maintenance import MaintenanceHistory

    if current_user.role not in [UserRole.ADMIN, UserRole.GERENTE, UserRole.GERENTE_INFRA]:
        return RedirectResponse(url=f"/manutencao-preventiva/ordens/{order_id}", status_code=303)

    order = await pm_crud.maintenance_order.get(db, id=order_id)
    if not order or order.status in [OrderStatus.CONCLUIDA, OrderStatus.CANCELADA]:
        return RedirectResponse(url=f"/manutencao-preventiva/ordens/{order_id}", status_code=303)

    status_anterior = order.status.value
    order.status = OrderStatus.CANCELADA
    db.add(order)

    desc = f"Ordem cancelada por {current_user.nome}"
    if motivo:
        desc += f". Motivo: {motivo}"

    history = MaintenanceHistory(
        order_id=order.id,
        acao="Ordem Cancelada",
        descricao=desc,
        usuario_id=current_user.id,
        status_anterior=status_anterior,
        status_novo=OrderStatus.CANCELADA.value
    )
    db.add(history)
    await db.commit()

    return RedirectResponse(url=f"/manutencao-preventiva/ordens/{order_id}", status_code=303)


# --- Detalhes do Plano de Manutenção ---

@router.get("/planos/{plan_id}", response_class=HTMLResponse)
async def plan_detail(
    request: Request,
    plan_id: int,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Página de detalhes do plano de manutenção"""
    plan = await pm_crud.maintenance_plan.get(db, id=plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plano não encontrado")

    # Obter ordens do plano
    stmt = (
        select(MaintenanceOrder)
        .options(
            selectinload(MaintenanceOrder.asset),
            selectinload(MaintenanceOrder.tecnico)
        )
        .filter(MaintenanceOrder.plan_id == plan_id)
        .order_by(MaintenanceOrder.data_abertura.desc())
        .limit(20)
    )
    result = await db.execute(stmt)
    orders = result.scalars().all()

    # Obter todos os assets para vincular
    all_assets = await db.execute(select(Asset).order_by(Asset.nome))
    all_assets = all_assets.scalars().all()

    return templates.TemplateResponse("preventive_maintenance/plan_detail.html", {
        "request": request,
        "user": current_user,
        "plan": plan,
        "orders": orders,
        "all_assets": all_assets,
        "title": f"Plano: {plan.codigo}"
    })


# --- Gerenciamento de Checklists ---

@router.post("/planos/{plan_id}/checklists")
async def add_checklist(
    plan_id: int,
    nome: Annotated[str, Form()],
    current_user: Annotated[User, Depends(get_active_user_web)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
):
    """Adicionar checklist a um plano"""
    plan = await pm_crud.maintenance_plan.get(db, id=plan_id)
    if not plan:
        raise HTTPException(status_code=404)

    # Determinar ordem do novo checklist
    existing = await pm_crud.maintenance_checklist.get_by_plan(db, plan_id=plan_id)
    next_order = len(existing)

    checklist = MaintenanceChecklist(
        plan_id=plan_id,
        nome=nome,
        ordem=next_order
    )
    db.add(checklist)
    await db.commit()

    return RedirectResponse(url=f"/manutencao-preventiva/planos/{plan_id}", status_code=303)


@router.post("/planos/{plan_id}/checklists/{checklist_id}/items")
async def add_checklist_item(
    plan_id: int,
    checklist_id: int,
    descricao: Annotated[str, Form()],
    obrigatorio: Annotated[Optional[str], Form()] = None,
    requer_foto: Annotated[Optional[str], Form()] = None,
    redirect_to: Annotated[Optional[str], Form()] = None,
    current_user: Annotated[User, Depends(get_active_user_web)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
):
    """Adicionar item a um checklist"""
    from app.models.preventive_maintenance import MaintenanceChecklistItem

    checklist = await pm_crud.maintenance_checklist.get(db, id=checklist_id)
    if not checklist or checklist.plan_id != plan_id:
        raise HTTPException(status_code=404)

    existing_items = await pm_crud.maintenance_checklist_item.get_by_checklist(db, checklist_id=checklist_id)
    next_order = len(existing_items)

    item = MaintenanceChecklistItem(
        checklist_id=checklist_id,
        descricao=descricao,
        obrigatorio=obrigatorio == "on",
        requer_foto=requer_foto == "on",
        ordem=next_order
    )
    db.add(item)
    await db.commit()

    # Redirecionar para a tela de origem (checklists global ou detalhe do plano)
    if redirect_to == "checklists":
        return RedirectResponse(url=f"/manutencao-preventiva/checklists?plan_id={plan_id}", status_code=303)
    return RedirectResponse(url=f"/manutencao-preventiva/planos/{plan_id}", status_code=303)


@router.post("/planos/{plan_id}/checklists/{checklist_id}/delete")
async def delete_checklist(
    plan_id: int,
    checklist_id: int,
    current_user: Annotated[User, Depends(get_active_user_web)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
):
    """Excluir um checklist"""
    if current_user.role not in [UserRole.ADMIN, UserRole.GERENTE, UserRole.GERENTE_INFRA]:
        return RedirectResponse(url=f"/manutencao-preventiva/planos/{plan_id}", status_code=303)

    await pm_crud.maintenance_checklist.remove(db, id=checklist_id)
    return RedirectResponse(url=f"/manutencao-preventiva/planos/{plan_id}", status_code=303)


@router.post("/planos/{plan_id}/checklists/{checklist_id}/items/{item_id}/delete")
async def delete_checklist_item(
    plan_id: int,
    checklist_id: int,
    item_id: int,
    current_user: Annotated[User, Depends(get_active_user_web)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
):
    """Excluir um item de checklist"""
    await pm_crud.maintenance_checklist_item.remove(db, id=item_id)
    return RedirectResponse(url=f"/manutencao-preventiva/planos/{plan_id}", status_code=303)


# --- Vincular Assets ao Plano ---

@router.post("/planos/{plan_id}/assets")
async def add_plan_asset(
    plan_id: int,
    asset_id: Annotated[int, Form()],
    current_user: Annotated[User, Depends(get_active_user_web)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
):
    """Vincular um ativo a um plano de manutenção"""
    from app.models.preventive_maintenance import MaintenancePlanAsset

    # Verificar se já existe
    existing = await pm_crud.maintenance_plan_asset.get_by_plan_and_asset(db, plan_id=plan_id, asset_id=asset_id)
    if not existing:
        link = MaintenancePlanAsset(plan_id=plan_id, asset_id=asset_id)
        db.add(link)
        await db.commit()

    return RedirectResponse(url=f"/manutencao-preventiva/planos/{plan_id}", status_code=303)


@router.post("/planos/{plan_id}/assets/{link_id}/delete")
async def remove_plan_asset(
    plan_id: int,
    link_id: int,
    current_user: Annotated[User, Depends(get_active_user_web)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
):
    """Remover vínculo de ativo de um plano"""
    await pm_crud.maintenance_plan_asset.remove(db, id=link_id)
    return RedirectResponse(url=f"/manutencao-preventiva/planos/{plan_id}", status_code=303)


# --- Execução de Checklist na Ordem ---

@router.post("/ordens/{order_id}/executar-checklist")
async def execute_checklist_item(
    request: Request,
    order_id: int,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Marcar item de checklist como concluído durante a execução da ordem"""
    import os
    import shutil
    import uuid
    from fastapi import UploadFile
    from app.models.preventive_maintenance import MaintenanceExecution, MaintenanceChecklistItem, MaintenancePhoto, PhotoType

    form = await request.form()
    
    checklist_item_id_str = form.get("checklist_item_id")
    if not checklist_item_id_str:
        return RedirectResponse(url=f"/manutencao-preventiva/ordens/{order_id}", status_code=303)
        
    checklist_item_id = int(checklist_item_id_str)
    concluido = form.get("concluido")
    observacao = form.get("observacao")
    foto = form.get("foto")

    # Verificar se já existe execução para este item nesta ordem
    stmt = select(MaintenanceExecution).filter(
        MaintenanceExecution.order_id == order_id,
        MaintenanceExecution.checklist_item_id == checklist_item_id
    )
    result = await db.execute(stmt)
    execution = result.scalar_one_or_none()

    is_done = concluido == "on"

    # Verificar se o item requer foto e se ela foi enviada
    item_stmt = select(MaintenanceChecklistItem).filter(MaintenanceChecklistItem.id == checklist_item_id)
    item_res = await db.execute(item_stmt)
    check_item = item_res.scalar_one_or_none()

    has_valid_photo = hasattr(foto, "filename") and bool(foto.filename)

    if check_item and check_item.requer_foto and is_done and not has_valid_photo:
        # Se for marcar como concluído, mas falta a foto que é obrigatória
        error_msg = f"A foto é obrigatória para o item: {check_item.descricao}"
        return RedirectResponse(url=f"/manutencao-preventiva/ordens/{order_id}?error={error_msg}", status_code=303)

    if execution:
        execution.concluido = is_done
        execution.observacao = observacao if isinstance(observacao, str) else None
        execution.data_execucao = now_sp()
        execution.executado_por_id = current_user.id
    else:
        execution = MaintenanceExecution(
            order_id=order_id,
            checklist_item_id=checklist_item_id,
            concluido=is_done,
            observacao=observacao if isinstance(observacao, str) else None,
            data_execucao=now_sp(),
            executado_por_id=current_user.id
        )
        db.add(execution)

    await db.flush() # Gerar o execution.id caso seja novo

    # Lidar com o upload da foto se fornecida
    if has_valid_photo and is_done:
        upload_dir = "static/uploads/maintenance"
        os.makedirs(upload_dir, exist_ok=True)
        ext = os.path.splitext(foto.filename)[1]
        unique_filename = f"os_{order_id}_exec_{execution.id}_{uuid.uuid4().hex}{ext}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(foto.file, buffer)
            
        foto_url = f"/{file_path}"
        
        photo = MaintenancePhoto(
            order_id=order_id,
            execution_id=execution.id,
            tipo=PhotoType.DURANTE,
            caminho_arquivo=foto_url,
            descricao=f"Evidência do checklist: {check_item.descricao if check_item else 'Item'}",
            upload_por_id=current_user.id
        )
        db.add(photo)

    await db.commit()
    return RedirectResponse(url=f"/manutencao-preventiva/ordens/{order_id}", status_code=303)


# --- Histórico da Ordem ---

@router.get("/ordens/{order_id}/historico", response_class=HTMLResponse)
async def order_history(
    request: Request,
    order_id: int,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Visualizar histórico completo da ordem"""
    order = await pm_crud.maintenance_order.get(db, id=order_id)
    if not order:
        raise HTTPException(status_code=404)

    history = await pm_crud.maintenance_history.get_by_order(db, order_id=order_id)

    return templates.TemplateResponse("preventive_maintenance/order_history.html", {
        "request": request,
        "user": current_user,
        "order": order,
        "history": history,
        "title": f"Histórico: {order.numero}"
    })


# --- Edição e Exclusão de Planos de Manutenção ---

@router.get("/planos/{plan_id}/editar", response_class=HTMLResponse)
async def edit_plan_form(
    request: Request,
    plan_id: int,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)],
    error: Optional[str] = None
):
    """Formulário para edição de plano de manutenção"""
    plan = await pm_crud.maintenance_plan.get(db, id=plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plano não encontrado")

    from app.models.preventive_maintenance import MaintenancePeriodicity

    return templates.TemplateResponse("preventive_maintenance/plan_edit.html", {
        "request": request,
        "user": current_user,
        "plan": plan,
        "maintenance_types": [mt.value for mt in MaintenanceType],
        "periodicities": [p.value for p in MaintenancePeriodicity],
        "maintenance_priorities": [mp.value for mp in MaintenancePriority],
        "maintenance_criticalities": [mc.value for mc in MaintenanceCriticality],
        "error": error,
        "title": f"Editar Plano: {plan.codigo}"
    })


@router.post("/planos/{plan_id}/editar")
async def update_plan(
    plan_id: int,
    nome: Annotated[str, Form()],
    tipo: Annotated[str, Form()],
    periodicidade: Annotated[str, Form()],
    criticidade: Annotated[str, Form()],
    descricao: Annotated[str, Form()],
    ativo: Annotated[str, Form()],
    dias_personalizado: Annotated[Optional[str], Form()] = None,
    current_user: Annotated[User, Depends(get_active_user_web)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
):
    """Atualiza as informações de um plano de manutenção"""
    from app.models.preventive_maintenance import MaintenancePeriodicity

    plan = await pm_crud.maintenance_plan.get(db, id=plan_id)
    if not plan:
        raise HTTPException(status_code=404)

    plan.nome = nome
    plan.tipo = MaintenanceType(tipo)
    plan.periodicidade = MaintenancePeriodicity(periodicidade)
    plan.criticidade = MaintenanceCriticality(criticidade)
    plan.descricao = descricao
    plan.ativo = ativo == "true"
    plan.dias_personalizado = int(dias_personalizado) if dias_personalizado and periodicidade == "Personalizada" else None

    db.add(plan)
    await db.commit()

    return RedirectResponse(url=f"/manutencao-preventiva/planos/{plan.id}", status_code=303)


@router.post("/planos/{plan_id}/delete")
async def delete_plan(
    plan_id: int,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Exclui um plano de manutenção se não houver ordens ativas/concluídas vinculadas"""
    if current_user.role not in [UserRole.ADMIN, UserRole.GERENTE, UserRole.GERENTE_INFRA]:
        raise HTTPException(status_code=403, detail="Não autorizado")

    plan = await pm_crud.maintenance_plan.get(db, id=plan_id)
    if not plan:
        raise HTTPException(status_code=404)

    # Verificar se existem ordens não canceladas
    stmt = (
        select(func.count(MaintenanceOrder.id))
        .filter(MaintenanceOrder.plan_id == plan_id)
        .filter(MaintenanceOrder.status != OrderStatus.CANCELADA)
    )
    result = await db.execute(stmt)
    active_orders_count = result.scalar() or 0

    if active_orders_count > 0:
        error_msg = "Não é possível excluir o plano porque existem ordens de serviço ativas ou concluídas associadas a ele. Recomendamos inativar o plano."
        return RedirectResponse(
            url=f"/manutencao-preventiva/planos/{plan_id}/editar?error={error_msg}",
            status_code=303
        )

    # Deletar manualmente as notificações vinculadas ao plano ou às suas ordens antes de excluir o plano
    from sqlalchemy import delete
    from app.models.preventive_maintenance import MaintenanceNotification, MaintenanceOrder
    
    order_ids_stmt = select(MaintenanceOrder.id).filter(MaintenanceOrder.plan_id == plan_id)
    order_ids_res = await db.execute(order_ids_stmt)
    order_ids = order_ids_res.scalars().all()
    if order_ids:
        await db.execute(delete(MaintenanceNotification).where(MaintenanceNotification.order_id.in_(order_ids)))
        
    await db.execute(delete(MaintenanceNotification).where(MaintenanceNotification.plan_id == plan_id))

    await pm_crud.maintenance_plan.remove(db, id=plan_id)
    return RedirectResponse(url="/manutencao-preventiva/planos", status_code=303)


# --- Edição e Exclusão de Ordens de Serviço ---

@router.get("/ordens/{order_id}/editar", response_class=HTMLResponse)
async def edit_order_form(
    request: Request,
    order_id: int,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)],
    error: Optional[str] = None
):
    """Formulário para edição de ordem de serviço"""
    stmt = (
        select(MaintenanceOrder)
        .options(selectinload(MaintenanceOrder.asset))
        .filter(MaintenanceOrder.id == order_id)
    )
    res = await db.execute(stmt)
    order = res.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Ordem não encontrada")

    # Obter lista de técnicos possíveis para delegar
    stmt_tec = select(User).filter(User.role.in_([UserRole.ADMIN, UserRole.GERENTE, UserRole.TECNICO, UserRole.GERENTE_INFRA]))
    res_tec = await db.execute(stmt_tec)
    tecnicos = res_tec.scalars().all()

    return templates.TemplateResponse("preventive_maintenance/order_edit.html", {
        "request": request,
        "user": current_user,
        "order": order,
        "tecnicos": tecnicos,
        "maintenance_types": [mt.value for mt in MaintenanceType],
        "priorities": [pr.value for pr in MaintenancePriority],
        "criticalities": [cr.value for cr in MaintenanceCriticality],
        "statuses": [st for st in OrderStatus],
        "error": error,
        "title": f"Editar OS: {order.numero}"
    })


@router.post("/ordens/{order_id}/editar")
async def update_order(
    order_id: int,
    tipo: Annotated[str, Form()],
    status: Annotated[str, Form()],
    prioridade: Annotated[str, Form()],
    criticidade: Annotated[str, Form()],
    observacoes: Annotated[str, Form()],
    tecnico_id: Annotated[Optional[str], Form()] = None,
    data_agendada: Annotated[Optional[str], Form()] = None,
    current_user: Annotated[User, Depends(get_active_user_web)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
):
    """Atualiza as informações de uma ordem de serviço"""
    order = await pm_crud.maintenance_order.get(db, id=order_id)
    if not order:
        raise HTTPException(status_code=404)

    # Guardar status anterior e técnico anterior para histórico/notificação
    status_anterior = order.status.value
    tecnico_anterior_id = order.tecnico_id
    novo_status = OrderStatus(status)
    novo_tecnico_id = int(tecnico_id) if tecnico_id and tecnico_id.strip() else None

    order.tipo = MaintenanceType(tipo)
    order.status = novo_status
    order.prioridade = MaintenancePriority(prioridade)
    order.criticidade = MaintenanceCriticality(criticidade)
    order.observacoes = observacoes
    order.tecnico_id = novo_tecnico_id
    order.data_agendada = datetime.fromisoformat(data_agendada) if data_agendada and data_agendada.strip() else None

    db.add(order)

    # Se mudou de status diretamente no form, registrar histórico
    if status_anterior != novo_status.value:
        from app.models.preventive_maintenance import MaintenanceHistory
        history = MaintenanceHistory(
            order_id=order.id,
            acao="Edição de Ordem",
            descricao=f"Ordem atualizada administrativamente por {current_user.nome}. Status alterado.",
            usuario_id=current_user.id,
            status_anterior=status_anterior,
            status_novo=novo_status.value
        )
        db.add(history)

    await db.commit()

    # Disparar notificação se o técnico mudou e agora está definido
    if novo_tecnico_id and novo_tecnico_id != tecnico_anterior_id:
        try:
            from app.models.user import User
            from app.models.asset import Asset
            from app.services.notification_service import notification_service
            
            tech_res = await db.execute(select(User).filter(User.id == novo_tecnico_id))
            tech = tech_res.scalar_one_or_none()
            
            asset_res = await db.execute(select(Asset).filter(Asset.id == order.asset_id))
            asset = asset_res.scalar_one_or_none()
            
            if tech and asset:
                await notification_service.notify_order_assigned(
                    db=db,
                    order_id=order.id,
                    order_code=order.numero,
                    technician_id=tech.id,
                    technician_email=tech.email,
                    asset_name=asset.nome,
                    priority=order.prioridade.value,
                    data_agendada=order.data_agendada
                )
                await db.commit() # Commita a notificação criada
        except Exception as e:
            print(f"[NOTIFICATION ERROR] Falha ao notificar técnico na reatribuição: {e}")

    return RedirectResponse(url=f"/manutencao-preventiva/ordens/{order.id}", status_code=303)


@router.post("/ordens/{order_id}/delete")
async def delete_order(
    order_id: int,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Exclui uma ordem de serviço se não estiver concluída"""
    if current_user.role not in [UserRole.ADMIN, UserRole.GERENTE, UserRole.GERENTE_INFRA]:
        raise HTTPException(status_code=403, detail="Não autorizado")

    order = await pm_crud.maintenance_order.get(db, id=order_id)
    if not order:
        raise HTTPException(status_code=404)

    # Se a ordem já foi concluída, bloquear exclusão para segurança do histórico
    if order.status == OrderStatus.CONCLUIDA:
        error_msg = "Não é possível excluir ordens de serviço com status Concluída."
        return RedirectResponse(
            url=f"/manutencao-preventiva/ordens/{order_id}/editar?error={error_msg}",
            status_code=303
        )

    # Deletar manualmente as notificações associadas antes da exclusão da ordem (evita erro de chave estrangeira)
    from sqlalchemy import delete
    from app.models.preventive_maintenance import MaintenanceNotification
    await db.execute(delete(MaintenanceNotification).where(MaintenanceNotification.order_id == order_id))

    await pm_crud.maintenance_order.remove(db, id=order_id)
    return RedirectResponse(url="/manutencao-preventiva/ordens", status_code=303)


# --- Gerenciamento de Materiais nas Ordens ---

@router.post("/ordens/{order_id}/materiais")
async def add_order_material(
    order_id: int,
    quantidade: Annotated[float, Form()],
    valor_unitario: Annotated[Optional[str], Form()] = None,
    produto: Annotated[Optional[str], Form()] = None,
    product_id: Annotated[Optional[str], Form()] = None,
    observacao: Annotated[Optional[str], Form()] = None,
    current_user: Annotated[User, Depends(get_active_user_web)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
):
    """Adiciona um material/peça de reposição à ordem de serviço e realiza a baixa no estoque"""
    from app.models.preventive_maintenance import MaintenanceMaterial, MaintenanceHistory
    from app.models.procurement import MaterialStock, PurchaseProduct, PurchaseOrderItem
    from app.services.procurement_service import handle_material_consumption_in_maintenance
    
    order = await pm_crud.maintenance_order.get(db, id=order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Ordem de serviço não encontrada")
        
    if order.status in [OrderStatus.CONCLUIDA, OrderStatus.CANCELADA]:
        raise HTTPException(status_code=400, detail="Não é possível alterar materiais de ordens concluídas ou canceladas")
        
    # Tratamento para campos vazios provenientes de formulário HTML
    parsed_product_id = None
    if product_id and product_id.strip():
        try:
            parsed_product_id = int(product_id.strip())
        except ValueError:
            raise HTTPException(status_code=400, detail="ID do produto inválido")
            
    parsed_valor_unitario = None
    if valor_unitario and valor_unitario.strip():
        try:
            parsed_valor_unitario = float(valor_unitario.replace(",", ".").strip())
        except ValueError:
            raise HTTPException(status_code=400, detail="Valor unitário inválido")

    final_produto = produto
    
    if parsed_product_id:
        # Se selecionou do estoque
        product_res = await db.execute(select(PurchaseProduct).filter(PurchaseProduct.id == parsed_product_id))
        product = product_res.scalar_one_or_none()
        if not product:
            raise HTTPException(status_code=400, detail="Produto do estoque não encontrado")
            
        final_produto = product.nome
        
        # Se valor unitário não foi informado para produto do estoque, busca a última compra
        if parsed_valor_unitario is None:
            po_item_stmt = select(PurchaseOrderItem.valor_unitario).filter(
                PurchaseOrderItem.product_id == parsed_product_id
            ).order_by(PurchaseOrderItem.id.desc()).limit(1)
            po_item_res = await db.execute(po_item_stmt)
            parsed_valor_unitario = po_item_res.scalar()
            if parsed_valor_unitario is None:
                parsed_valor_unitario = 0.0
            else:
                parsed_valor_unitario = float(parsed_valor_unitario)
        
        # Validar estoque
        stock_res = await db.execute(select(MaterialStock).filter(MaterialStock.product_id == parsed_product_id))
        stock_obj = stock_res.scalar_one_or_none()
        if not stock_obj or stock_obj.quantidade_saldo < quantidade:
            saldo_disp = stock_obj.quantidade_saldo if stock_obj else 0.0
            error_msg = f"Saldo de estoque insuficiente para o item '{product.nome}'. Disponível: {saldo_disp:.2f}"
            return RedirectResponse(url=f"/manutencao-preventiva/ordens/{order_id}?error={error_msg}", status_code=303)
            
        # Baixa no estoque
        await handle_material_consumption_in_maintenance(
            product_id=parsed_product_id,
            quantity=quantidade,
            db=db,
            current_user_id=current_user.id,
            maintenance_id=order_id
        )
    else:
        # Modo manual (sem vínculo de estoque) se produto_id for nulo e produto text foi fornecido
        if not final_produto:
            error_msg = "Selecione um produto do estoque ou informe a descrição."
            return RedirectResponse(url=f"/manutencao-preventiva/ordens/{order_id}?error={error_msg}", status_code=303)
            
        if parsed_valor_unitario is None:
            error_msg = "O valor unitário é obrigatório para materiais avulsos."
            return RedirectResponse(url=f"/manutencao-preventiva/ordens/{order_id}?error={error_msg}", status_code=303)
            
    valor_total = quantidade * parsed_valor_unitario
    
    material = MaintenanceMaterial(
        order_id=order_id,
        product_id=parsed_product_id,
        produto=final_produto,
        quantidade=quantidade,
        valor_unitario=parsed_valor_unitario,
        valor_total=valor_total,
        observacao=observacao
    )
    db.add(material)
    await db.flush() # Gerar ID temporário para logs
    
    # Recalcular custo total da OS (soma de todos os materiais)
    stmt = select(func.sum(MaintenanceMaterial.valor_total)).filter(MaintenanceMaterial.order_id == order_id)
    res = await db.execute(stmt)
    total_materials = res.scalar() or 0.0
    order.custo_total = float(total_materials)
    db.add(order)
    
    # Registrar no histórico da ordem
    history = MaintenanceHistory(
        order_id=order.id,
        acao="Material Adicionado",
        descricao=f"Material '{final_produto}' (Qtd: {quantidade:.2f}, R$ {parsed_valor_unitario:.2f}/un, Total: R$ {valor_total:.2f}) adicionado por {current_user.nome}.",
        usuario_id=current_user.id
    )
    db.add(history)
    
    await db.commit()
    return RedirectResponse(url=f"/manutencao-preventiva/ordens/{order_id}", status_code=303)


@router.post("/ordens/{order_id}/materiais/{material_id}/delete")
async def remove_order_material(
    order_id: int,
    material_id: int,
    current_user: Annotated[User, Depends(get_active_user_web)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
):
    """Remove um material/peça de reposição de uma ordem de serviço e estorna o estoque"""
    from app.models.preventive_maintenance import MaintenanceMaterial, MaintenanceHistory
    
    order = await pm_crud.maintenance_order.get(db, id=order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Ordem de serviço não encontrada")
        
    if order.status in [OrderStatus.CONCLUIDA, OrderStatus.CANCELADA]:
        raise HTTPException(status_code=400, detail="Não é possível alterar materiais de ordens concluídas ou canceladas")
        
    # Buscar material para obter detalhes para o histórico antes de remover
    material_stmt = select(MaintenanceMaterial).filter(MaintenanceMaterial.id == material_id)
    res_mat = await db.execute(material_stmt)
    material = res_mat.scalar_one_or_none()
    
    if not material:
        raise HTTPException(status_code=404, detail="Material não encontrado")
        
    produto = material.produto
    
    # Estornar do estoque se possuir product_id
    if material.product_id:
        from app.crud.procurement import create_or_update_stock
        await create_or_update_stock(
            db=db,
            product_id=material.product_id,
            quantidade=float(material.quantidade),
            tipo="Entrada",
            user_id=current_user.id,
            justificativa=f"Estorno de Material removido da OS ID {order_id}",
            origem_tabela="maintenance",
            origem_id=order_id
        )
        
    # Remover o material
    if material in order.materials:
        order.materials.remove(material)
    await db.delete(material)
    await db.flush()
    
    # Recalcular custo total da OS (soma dos materiais restantes)
    stmt = select(func.sum(MaintenanceMaterial.valor_total)).filter(MaintenanceMaterial.order_id == order_id)
    res = await db.execute(stmt)
    total_materials = res.scalar() or 0.0
    order.custo_total = float(total_materials)
    db.add(order)
    
    # Registrar no histórico da ordem
    history = MaintenanceHistory(
        order_id=order.id,
        acao="Material Removido",
        descricao=f"Material '{produto}' removido da ordem por {current_user.nome}.",
        usuario_id=current_user.id
    )
    db.add(history)
    
    await db.commit()
    return RedirectResponse(url=f"/manutencao-preventiva/ordens/{order_id}", status_code=303)


# --- Gerenciamento de Fotos das Ordens ---

@router.post("/ordens/{order_id}/fotos")
async def upload_order_photo(
    order_id: int,
    foto: Annotated[UploadFile, File()],
    tipo: Annotated[str, Form()],
    descricao: Annotated[Optional[str], Form()] = None,
    current_user: Annotated[User, Depends(get_active_user_web)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
):
    """Realiza o upload de uma foto de manutenção"""
    import shutil
    import uuid
    from app.models.preventive_maintenance import MaintenancePhoto, MaintenanceHistory, PhotoType
    
    order = await pm_crud.maintenance_order.get(db, id=order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Ordem de serviço não encontrada")
        
    if order.status in [OrderStatus.CONCLUIDA, OrderStatus.CANCELADA]:
        raise HTTPException(status_code=400, detail="Não é possível adicionar fotos a ordens concluídas ou canceladas")
        
    if not foto or not foto.filename:
        raise HTTPException(status_code=400, detail="Arquivo de foto inválido")
        
    # Garantir que a pasta de uploads de manutenção existe
    upload_dir = "static/uploads/maintenance"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Criar nome de arquivo único
    ext = os.path.splitext(foto.filename)[1]
    unique_filename = f"os_{order_id}_{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(upload_dir, unique_filename)
    
    # Salvar o arquivo no disco
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(foto.file, buffer)
        
    foto_url = f"/{file_path}"
    
    # Criar registro de foto no banco
    photo = MaintenancePhoto(
        order_id=order_id,
        tipo=PhotoType(tipo),
        caminho_arquivo=foto_url,
        descricao=descricao,
        upload_por_id=current_user.id
    )
    db.add(photo)
    
    # Registrar no histórico da ordem
    history = MaintenanceHistory(
        order_id=order.id,
        acao="Foto Adicionada",
        descricao=f"Foto da etapa '{tipo}' adicionada por {current_user.nome}." + (f" Descrição: {descricao}" if descricao else ""),
        usuario_id=current_user.id
    )
    db.add(history)
    
    await db.commit()
    return RedirectResponse(url=f"/manutencao-preventiva/ordens/{order_id}", status_code=303)


@router.post("/ordens/{order_id}/fotos/{photo_id}/delete")
async def delete_order_photo(
    order_id: int,
    photo_id: int,
    current_user: Annotated[User, Depends(get_active_user_web)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
):
    """Remove uma foto de manutenção e seu arquivo correspondente do servidor"""
    from app.models.preventive_maintenance import MaintenancePhoto, MaintenanceHistory
    
    order = await pm_crud.maintenance_order.get(db, id=order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Ordem de serviço não encontrada")
        
    if order.status in [OrderStatus.CONCLUIDA, OrderStatus.CANCELADA]:
        raise HTTPException(status_code=400, detail="Não é possível remover fotos de ordens concluídas ou canceladas")
        
    # Buscar foto
    photo_stmt = select(MaintenancePhoto).filter(MaintenancePhoto.id == photo_id)
    res_photo = await db.execute(photo_stmt)
    photo = res_photo.scalar_one_or_none()
    
    if not photo:
        raise HTTPException(status_code=404, detail="Foto não encontrada")
        
    tipo = photo.tipo.value
    caminho = photo.caminho_arquivo
    
    # Remover o arquivo físico (remover a barra inicial / se houver para apontar para o diretório correto)
    local_path = caminho.lstrip("/")
    if os.path.exists(local_path):
        try:
            os.remove(local_path)
        except Exception:
            pass # Ignora falhas de deleção física para evitar travar o fluxo
            
    # Remover do banco
    await db.delete(photo)
    
    # Registrar no histórico da ordem
    history = MaintenanceHistory(
        order_id=order.id,
        acao="Foto Removida",
        descricao=f"Foto da etapa '{tipo}' removida da ordem por {current_user.nome}.",
        usuario_id=current_user.id
    )
    db.add(history)
    
    await db.commit()
    return RedirectResponse(url=f"/manutencao-preventiva/ordens/{order_id}", status_code=303)
