
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
    
    # Pending Solicitations
    pending_solicitations = await db.scalar(select(func.count(Solicitacao.id)).filter(Solicitacao.status == StatusSolicitacao.PENDENTE))

    # Context data
    context = {
        "request": request,
        "user": current_user,
        "stats": {
            "total_assets": total_assets or 0,
            "available_assets": available_assets or 0,
            "pending_solicitations": pending_solicitations or 0
        },
        "title": "Dashboard"
    }

    # Admin specific data
    if current_user.role.value.lower() in ["admin", "gerente_ti"]:
        # Pending Users to Approve
        pending_users_result = await db.execute(select(User).filter(User.is_active == False))
        context["pending_users_list"] = pending_users_result.scalars().all()

        # Pending Solicitations (Full details for table) - with eager loading
        pending_solicitations_result = await db.execute(
            select(Solicitacao)
            .options(selectinload(Solicitacao.asset), selectinload(Solicitacao.solicitante))
            .filter(Solicitacao.status == StatusSolicitacao.PENDENTE)
            .order_by(Solicitacao.data_solicitacao)
        )
        context["pending_solicitations_list"] = pending_solicitations_result.scalars().all()

    return templates.TemplateResponse("dashboard.html", context)

