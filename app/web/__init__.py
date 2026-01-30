
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
