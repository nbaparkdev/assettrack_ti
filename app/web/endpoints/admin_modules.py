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
    """Página para gerenciar a ativação/desativação de módulos do sistema e permissões de menus"""
    pm_enabled_str = await system_settings.get_setting(db, "preventive_maintenance_enabled", default_value="true")
    pm_enabled = pm_enabled_str.lower() == "true"
    
    purchases_enabled_str = await system_settings.get_setting(db, "purchases_enabled", default_value="true")
    purchases_enabled = purchases_enabled_str.lower() == "true"
    
    # Carregar permissões de menu
    import json
    perms_str = await system_settings.get_setting(db, "menu_permissions")
    if perms_str:
        try:
            menu_permissions = json.loads(perms_str)
        except Exception:
            menu_permissions = {}
    else:
        menu_permissions = {}
        
    # Valores padrão de permissões
    default_permissions = {
        "ativos": ["admin", "gerente_ti", "gerente_infra", "tecnico", "comprador", "usuario_comum"],
        "fornecedores": ["admin", "gerente_ti", "gerente_infra", "comprador"],
        "manutencao": ["admin", "gerente_ti", "gerente_infra", "tecnico"],
        "tickets": ["admin", "gerente_ti", "gerente_infra", "tecnico", "comprador", "usuario_comum"],
        "compras": ["admin", "gerente_ti", "gerente_infra", "comprador"],
        "relatorios": ["admin", "gerente_ti", "gerente_infra", "comprador"],
        "usuarios": ["admin", "gerente_ti", "gerente_infra"],
        "backup": ["admin", "gerente_ti", "gerente_infra"]
    }
    for k, v in default_permissions.items():
        if k not in menu_permissions:
            menu_permissions[k] = v

    success = request.query_params.get("success") == "1"

    # Definir listas de perfis e menus para a matriz
    roles = [
        {"value": "admin", "label": "Administrador"},
        {"value": "gerente_ti", "label": "Gerente TI"},
        {"value": "gerente_infra", "label": "Gerente Infra"},
        {"value": "tecnico", "label": "Técnico"},
        {"value": "comprador", "label": "Comprador"},
        {"value": "usuario_comum", "label": "Usuário Comum"}
    ]
    
    menus = [
        {"key": "ativos", "label": "Ativos & Patrimônio"},
        {"key": "fornecedores", "label": "Fornecedores"},
        {"key": "manutencao", "label": "Manutenção Preventiva"},
        {"key": "tickets", "label": "Service Desk / Tickets"},
        {"key": "compras", "label": "Compras & Almoxarifado"},
        {"key": "relatorios", "label": "Relatórios"},
        {"key": "usuarios", "label": "Gerenciar Usuários (Admin)"},
        {"key": "backup", "label": "Backup do Sistema (Admin)"}
    ]

    return templates.TemplateResponse("admin/modules.html", {
        "request": request,
        "user": current_user,
        "pm_enabled": pm_enabled,
        "purchases_enabled": purchases_enabled,
        "menu_permissions": menu_permissions,
        "roles": roles,
        "menus": menus,
        "success": success,
        "title": "Gerenciar Módulos e Acessos"
    })

@router.post("/modulos")
async def gerenciar_modulos_submit(
    request: Request,
    current_user: Annotated[User, Depends(get_admin_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)],
    preventive_maintenance_enabled: Optional[str] = Form(None),
    purchases_enabled: Optional[str] = Form(None)
):
    # Salvar módulos
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

    # Processar permissões do menu
    form_data = await request.form()
    menus = ["ativos", "fornecedores", "manutencao", "tickets", "compras", "relatorios", "usuarios", "backup"]
    
    new_permissions = {m: [] for m in menus}
    for key, val in form_data.items():
        if key.startswith("menu_"):
            parts = key.split("_", 2)
            if len(parts) >= 3:
                menu_key = parts[1]
                role_value = parts[2]
                if menu_key in new_permissions:
                    new_permissions[menu_key].append(role_value)
                    
    # Sempre garantir que o admin tenha acesso a tudo para evitar lock-out acidental
    for m in menus:
        if "admin" not in new_permissions[m]:
            new_permissions[m].append("admin")

    import json
    perms_str = json.dumps(new_permissions)
    await system_settings.set_setting(
        db=db,
        setting_key="menu_permissions",
        setting_value=perms_str,
        descricao="Mapeamento de permissões de acesso por menu e perfil"
    )
    request.app.state.menu_permissions = new_permissions

    return RedirectResponse(url="/admin/modulos?success=1", status_code=status.HTTP_303_SEE_OTHER)

