
# app/web/endpoints/dashboard.py
from typing import Annotated
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.web.dependencies import get_active_user_web
from app.models.user import User
from app.models.asset import Asset, AssetStatus
from app.models.transaction import Solicitacao, StatusSolicitacao
from app.database import get_db

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    # Total Assets
    total_assets = await db.scalar(select(func.count(Asset.id)))
    
    # Available Assets
    available_assets = await db.scalar(select(func.count(Asset.id)).filter(Asset.status == AssetStatus.DISPONIVEL))

    # In Use Assets
    in_use_assets = await db.scalar(select(func.count(Asset.id)).filter(Asset.status == AssetStatus.EM_USO))

    # Maintenance Assets
    maintenance_assets = await db.scalar(select(func.count(Asset.id)).filter(Asset.status == AssetStatus.MANUTENCAO))
    
    # Pending Solicitations (Tickets)
    pending_solicitations = await db.scalar(select(func.count(Solicitacao.id)).filter(Solicitacao.status == StatusSolicitacao.PENDENTE))

    user_role = str(current_user.role.value).lower()

    # Pending Maintenance Requests (for alert)
    pending_maintenance_count = 0
    pending_tickets_count = 0
    # Maintenance and Tickets alerts for staff
    if user_role in ["admin", "gerente_ti", "tecnico", "gerente_infra"]:
        from app.models.maintenance_request import SolicitacaoManutencao, StatusSolicitacaoManutencao
        from app.models.service_desk import ServiceTicket, ServiceStatus
        
        pending_maintenance_count = await db.scalar(
            select(func.count(SolicitacaoManutencao.id))
            .filter(SolicitacaoManutencao.status == StatusSolicitacaoManutencao.PENDENTE)
        )
        
        pending_tickets_count = await db.scalar(
            select(func.count(ServiceTicket.id))
            .filter(ServiceTicket.status == ServiceStatus.ABERTO)
        )

    # Context data
    context = {
        "request": request,
        "user": current_user,
        "stats": {
            "total_assets": total_assets or 0,
            "available_assets": available_assets or 0,
            "in_use_assets": in_use_assets or 0,
            "maintenance_assets": maintenance_assets or 0,
            "pending_solicitations": pending_solicitations or 0,
            "pending_maintenance": pending_maintenance_count or 0,
            "pending_tickets": pending_tickets_count or 0
        },
        "title": "Dashboard"
    }

    # Admin and Manager specific data (Users & Recent Deliveries)
    if user_role in ["admin", "gerente_ti", "gerente_infra", "comprador"]:
        # Expiring contracts alert
        purchases_enabled = getattr(request.app.state, "purchases_enabled", True)
        expiring_contracts_data = []
        if purchases_enabled and user_role in ["admin", "gerente_ti", "comprador"]:
            from app.models.procurement import PurchaseContract
            from datetime import datetime, timedelta
            limit_date = datetime.now() + timedelta(days=90)
            res = await db.execute(
                select(PurchaseContract)
                .options(selectinload(PurchaseContract.fornecedor))
                .filter(PurchaseContract.data_fim <= limit_date)
                .order_by(PurchaseContract.data_fim)
            )
            expiring_contracts = res.scalars().all()
            for c in expiring_contracts:
                dias = (c.data_fim - datetime.now()).days
                tag_color = "bg-gray-100 text-gray-800 border-gray-300"
                tag_text = f"{dias} dias"
                if dias < 0:
                    tag_color = "bg-red-200 text-red-900 border-red-500 font-extrabold"
                    tag_text = "Expirado"
                elif dias <= 7:
                    tag_color = "bg-red-100 text-red-800 border-red-400 font-bold"
                    tag_text = "Crítico (7 dias)"
                elif dias <= 15:
                    tag_color = "bg-orange-100 text-orange-800 border-orange-400 font-bold"
                    tag_text = "Alerta (15 dias)"
                elif dias <= 30:
                    tag_color = "bg-amber-100 text-amber-800 border-amber-400"
                    tag_text = "Atenção (30 dias)"
                elif dias <= 60:
                    tag_color = "bg-blue-100 text-blue-800 border-blue-400"
                    tag_text = "60 dias"
                elif dias <= 90:
                    tag_color = "bg-green-100 text-green-800 border-green-400"
                    tag_text = "90 dias"
                    
                expiring_contracts_data.append({
                    "contract": c,
                    "dias": dias,
                    "tag_color": tag_color,
                    "tag_text": tag_text
                })
        context["expiring_contracts"] = expiring_contracts_data

        # Pending Users to Approve
        pending_users_result = await db.execute(select(User).filter(User.is_active == False))
        context["pending_users_list"] = pending_users_result.scalars().all()

        # Recent Deliveries (Last 5)
        from app.models.maintenance_request import SolicitacaoManutencao, StatusSolicitacaoManutencao
        recent_deliveries_result = await db.execute(
            select(SolicitacaoManutencao)
            .options(
                selectinload(SolicitacaoManutencao.asset), 
                selectinload(SolicitacaoManutencao.solicitante),
                selectinload(SolicitacaoManutencao.responsavel)
            )
            .filter(SolicitacaoManutencao.status.in_([
                StatusSolicitacaoManutencao.ENTREGUE, 
                StatusSolicitacaoManutencao.CONCLUIDA
            ]))
            .order_by(SolicitacaoManutencao.data_conclusao_tecnico.desc()) 
            .limit(5)
        )
        context["recent_deliveries"] = recent_deliveries_result.scalars().all()

    # Admin, Manager AND Technician (Solicitations of Assets)
    if user_role in ["admin", "gerente_ti", "tecnico", "gerente_infra"]:
        # Pending Solicitations (Full details for table) - with eager loading
        pending_solicitations_result = await db.execute(
            select(Solicitacao)
            .options(selectinload(Solicitacao.asset), selectinload(Solicitacao.solicitante))
            .filter(Solicitacao.status == StatusSolicitacao.PENDENTE)
            .order_by(Solicitacao.data_solicitacao)
        )
        context["pending_solicitations_list"] = pending_solicitations_result.scalars().all()

        # Approved Solicitations (Waiting for Delivery)
        approved_solicitations_result = await db.execute(
            select(Solicitacao)
            .options(selectinload(Solicitacao.asset), selectinload(Solicitacao.solicitante))
            .filter(Solicitacao.status == StatusSolicitacao.APROVADA)
            .order_by(Solicitacao.data_aprovacao.desc())
        )
        context["approved_solicitations_list"] = approved_solicitations_result.scalars().all()

    return templates.TemplateResponse("dashboard.html", context)

