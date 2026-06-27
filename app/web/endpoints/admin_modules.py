# app/web/endpoints/admin_modules.py
from typing import Annotated, Optional
from fastapi import APIRouter, Request, Depends, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.web.dependencies import get_admin_user_web
from app.models.user import User
from app.crud.system_settings import system_settings

router = APIRouter(dependencies=[Depends(get_admin_user_web)])
templates = Jinja2Templates(directory="app/templates")

@router.get("/modulos", response_class=HTMLResponse)
async def gerenciar_modulos_page(
    request: Request,
    current_user: Annotated[User, Depends(get_admin_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Página para gerenciar a ativação/desativação de módulos do sistema"""
    pm_enabled_str = await system_settings.get_setting(db, "preventive_maintenance_enabled", default_value="true")
    pm_enabled = pm_enabled_str.lower() == "true"
    
    purchases_enabled_str = await system_settings.get_setting(db, "purchases_enabled", default_value="true")
    purchases_enabled = purchases_enabled_str.lower() == "true"
    
    success = request.query_params.get("success") == "1"

    return templates.TemplateResponse("admin/modules.html", {
        "request": request,
        "user": current_user,
        "pm_enabled": pm_enabled,
        "purchases_enabled": purchases_enabled,
        "success": success,
        "title": "Gerenciar Módulos"
    })

@router.post("/modulos")
async def gerenciar_modulos_submit(
    request: Request,
    current_user: Annotated[User, Depends(get_admin_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)],
    preventive_maintenance_enabled: Optional[str] = Form(None),
    purchases_enabled: Optional[str] = Form(None)
):
    # Se o checkbox/toggle não for marcado na requisição, ele vem como None
    enabled_val = "true" if preventive_maintenance_enabled == "on" else "false"
    await system_settings.set_setting(
        db=db,
        setting_key="preventive_maintenance_enabled",
        setting_value=enabled_val,
        descricao="Ativação do módulo de Manutenção Preventiva e Corretiva"
    )
    request.app.state.pm_enabled = (enabled_val == "true")

    pur_enabled_val = "true" if purchases_enabled == "on" else "false"
    await system_settings.set_setting(
        db=db,
        setting_key="purchases_enabled",
        setting_value=pur_enabled_val,
        descricao="Ativação do módulo de Compras (Procurement)"
    )
    request.app.state.purchases_enabled = (pur_enabled_val == "true")

    return RedirectResponse(url="/admin/modulos?success=1", status_code=status.HTTP_303_SEE_OTHER)

