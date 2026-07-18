
# app/web/__init__.py
from fastapi import APIRouter
from app.web.endpoints import auth, dashboard, assets, solicitacoes, movimentacoes, admin, users

web_router = APIRouter()
web_router.include_router(auth.router, tags=["web_auth"])
web_router.include_router(dashboard.router, tags=["web_dashboard"])
web_router.include_router(assets.router, prefix="/assets", tags=["web_assets"])
web_router.include_router(solicitacoes.router, prefix="/solicitacoes", tags=["web_solicitacoes"])
web_router.include_router(movimentacoes.router, prefix="/movimentacoes", tags=["web_movimentacoes"])
web_router.include_router(admin.router, prefix="/admin", tags=["web_admin"])
web_router.include_router(users.router, tags=["web_users"])
from app.web.endpoints import profile
web_router.include_router(profile.router, prefix="/profile", tags=["web_profile"])
from app.web.endpoints import setores
web_router.include_router(setores.router, prefix="/setores", tags=["web_setores"])
from app.web.endpoints import qr
web_router.include_router(qr.router, tags=["web_qr"])
from app.web.endpoints import maintenance_requests
web_router.include_router(maintenance_requests.router, tags=["web_maintenance_requests"])
from app.web.endpoints import help
web_router.include_router(help.router, tags=["web_help"])
from app.web.endpoints import service_desk
web_router.include_router(service_desk.router, prefix="/servicos", tags=["web_service_desk"])
from app.web.endpoints import suppliers
web_router.include_router(suppliers.router, prefix="/suppliers", tags=["web_suppliers"])
from app.web.endpoints import backup
web_router.include_router(backup.router, tags=["web_backup"])
from app.web.endpoints import preventive_maintenance
web_router.include_router(preventive_maintenance.router, prefix="/manutencao-preventiva", tags=["web_preventive_maintenance"])
from app.web.endpoints import admin_modules
web_router.include_router(admin_modules.router, prefix="/admin", tags=["web_admin_modules"])
from app.web.endpoints import procurement
web_router.include_router(procurement.router, prefix="/compras", tags=["web_procurement"])
from app.web.endpoints import ai_chat
web_router.include_router(ai_chat.router, tags=["web_ai_chat"])
from app.web.endpoints import admin_notifications
web_router.include_router(admin_notifications.router, tags=["web_admin_notifications"])
from app.web.endpoints import avisos
web_router.include_router(avisos.router, tags=["web_avisos"])
