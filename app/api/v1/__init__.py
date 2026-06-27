
# app/api/v1/__init__.py
from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, assets, solicitacoes, movimentacoes, qr, preventive_maintenance, api_procurement

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(assets.router, prefix="/assets", tags=["assets"])
api_router.include_router(solicitacoes.router, prefix="/solicitacoes", tags=["solicitacoes"])
api_router.include_router(movimentacoes.router, prefix="/movimentacoes", tags=["movimentacoes"])
api_router.include_router(qr.router, prefix="/qr", tags=["qr-code"])
api_router.include_router(preventive_maintenance.router, prefix="/preventive-maintenance", tags=["preventive-maintenance"])
api_router.include_router(api_procurement.router, prefix="/compras", tags=["compras"])


