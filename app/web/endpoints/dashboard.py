
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

    # Pending Maintenance Requests (for alert)
    pending_maintenance_count = 0
    if current_user.role.value.lower() in ["admin", "gerente_ti", "tecnico"]:
        from app.models.maintenance_request import SolicitacaoManutencao, StatusSolicitacaoManutencao
        pending_maintenance_count = await db.scalar(
            select(func.count(SolicitacaoManutencao.id))
            .filter(SolicitacaoManutencao.status == StatusSolicitacaoManutencao.PENDENTE)
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
            "pending_maintenance": pending_maintenance_count or 0
        },
        "title": "Dashboard"
    }

    # Admin and Manager specific data (Users & Recent Deliveries)
    if current_user.role.value.lower() in ["admin", "gerente_ti"]:
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
    if current_user.role.value.lower() in ["admin", "gerente_ti", "tecnico"]:
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

