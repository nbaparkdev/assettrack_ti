
from typing import Annotated, Optional
from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.web.dependencies import get_active_user_web
from app.models.user import User, UserRole
from app.models.transaction import Movimentacao
from app.models.asset import Asset
from app.database import get_db

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def list_movimentacoes(
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)],
    asset_id: Annotated[Optional[int], Query()] = None,
    tipo: Annotated[Optional[str], Query()] = None
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

