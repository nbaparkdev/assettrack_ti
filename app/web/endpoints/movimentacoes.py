
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.asset import Asset
from app.models.transaction import Movimentacao
from app.models.user import User
from app.web.dependencies import get_active_user_web

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def list_movimentacoes(
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)],
    asset_id: Annotated[int | None, Query()] = None,
    tipo: Annotated[str | None, Query()] = None
):
    """List movements with optional filters for asset and type"""
    
    # Build query with eager loading
    stmt = select(Movimentacao).options(
        selectinload(Movimentacao.asset),
        selectinload(Movimentacao.de_user),
        selectinload(Movimentacao.para_user)
    )
    
    # Filter by asset if provided
    asset_filter = None
    if asset_id:
        stmt = stmt.where(Movimentacao.asset_id == asset_id)
        # Fetch asset info for display
        asset_result = await db.execute(select(Asset).where(Asset.id == asset_id))
        asset_filter = asset_result.scalar_one_or_none()
    
    # Filter by type if provided
    if tipo:
        stmt = stmt.where(Movimentacao.tipo == tipo)

    # If common user, they can only see their own movements
    if str(current_user.role.value).lower() == 'usuario_comum':
        from sqlalchemy import or_
        stmt = stmt.where(
            or_(
                Movimentacao.de_user_id == current_user.id,
                Movimentacao.para_user_id == current_user.id
            )
        )
    
    # Order by date descending
    stmt = stmt.order_by(Movimentacao.data.desc())
    
    result = await db.execute(stmt)
    movimentacoes = result.scalars().all()
    
    return templates.TemplateResponse("movimentacoes/list.html", {
        "request": request,
        "user": current_user,
        "movimentacoes": movimentacoes,
        "asset_filter": asset_filter,
        "title": "Histórico de Movimentações"
    })

