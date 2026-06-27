# app/main.py
import os
import uvicorn
import logging
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from app.config import settings
from app.api.v1 import api_router
from app.database import engine, Base, get_db
from app.web import web_router
from app.web.endpoints import admin 
from app.core.rate_limit import limiter
import app.models
from slowapi.errors import RateLimitExceeded

# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

# Função para criar tabelas no startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup — cria tabelas
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Auto-migration de colunas para o Service Desk (transações isoladas)
    from sqlalchemy import text
    try:
        async with engine.connect() as conn:
            await conn.execution_options(isolation_level="AUTOCOMMIT")
            await conn.execute(text("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'COMPRADOR'"))
    except Exception:
        pass
            
    async with engine.begin() as conn:
        try:
            await conn.execute(text("ALTER TABLE service_tickets ADD COLUMN foto VARCHAR(255)"))
        except Exception:
            pass
    async with engine.begin() as conn:
        try:
            await conn.execute(text("ALTER TABLE service_ticket_interactions ADD COLUMN foto VARCHAR(255)"))
        except Exception:
            pass

    # Asset Categories - FK column
    async with engine.begin() as conn:
        try:
            await conn.execute(text("ALTER TABLE assets ADD COLUMN categoria_id INTEGER REFERENCES asset_categories(id)"))
        except Exception:
            pass

    # Asset - em_posse_de column
    async with engine.begin() as conn:
        try:
            await conn.execute(text("ALTER TABLE assets ADD COLUMN em_posse_de VARCHAR(255)"))
        except Exception:
            pass

    # Asset - bloqueado column
    async with engine.begin() as conn:
        try:
            await conn.execute(text("ALTER TABLE assets ADD COLUMN bloqueado BOOLEAN DEFAULT FALSE"))
        except Exception:
            pass

    # Adicionar 'comprador' ao enum userrole (PostgreSQL)
    async with engine.begin() as conn:
        try:
            await conn.execute(text("ALTER TYPE userrole ADD VALUE 'comprador'"))
        except Exception:
            pass

    # Iniciar agendador de manutenção preventiva em background
    import asyncio
    from app.services.maintenance_scheduler import start_maintenance_scheduler_loop
    
    # Executa a verificação imediatamente no startup e depois a cada 1 hora (3600s)
    scheduler_task = asyncio.create_task(start_maintenance_scheduler_loop(interval_seconds=3600))
    app.state.maintenance_scheduler_task = scheduler_task

    # Carregar configuração de system_settings
    from app.crud.system_settings import system_settings
    from app.database import SessionLocal
    async with SessionLocal() as session:
        try:
            val = await system_settings.get_setting(session, "preventive_maintenance_enabled", default_value="true")
            app.state.pm_enabled = (val.lower() == "true")
        except Exception:
            app.state.pm_enabled = True

        try:
            val_pur = await system_settings.get_setting(session, "purchases_enabled", default_value="true")
            app.state.purchases_enabled = (val_pur.lower() == "true")
        except Exception:
            app.state.purchases_enabled = True

    yield
    # Shutdown
    logger = logging.getLogger("app.main")
    logger.info("Cancelando agendador de manutenção preventiva...")
    scheduler_task.cancel()
    try:
        await scheduler_task
    except asyncio.CancelledError:
        pass
    
    await engine.dispose()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

@app.middleware("http")
async def add_module_state(request: Request, call_next):
    request.state.pm_enabled = getattr(request.app.state, "pm_enabled", True)
    request.state.purchases_enabled = getattr(request.app.state, "purchases_enabled", True)
    return await call_next(request)


# Templates instantiation
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Mount static files (always create directory first if not present to ensure mount is active)
static_dir = os.path.join(PROJECT_ROOT, "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Rate Limiter
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Muitas tentativas. Aguarde antes de tentar novamente."}
    )

@app.exception_handler(404)
async def custom_404_handler(request: Request, exc):
    return templates.TemplateResponse("errors/404.html", {
        "request": request,
        "title": "Página não Encontrada"
    }, status_code=404)

@app.exception_handler(500)
async def custom_500_handler(request: Request, exc):
    # Log error here if logger configured
    print(f"ERROR: {exc}") 
    return templates.TemplateResponse("errors/500.html", {
        "request": request,
        "title": "Erro Interno"
    }, status_code=500)

app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(web_router)

@app.get("/debug-db")
async def debug_db(db = Depends(get_db)):
    from sqlalchemy import select
    from app.models.system_settings import SystemSettings
    result = await db.execute(select(SystemSettings))
    settings_list = result.scalars().all()
    return [{"id": s.id, "setting_key": s.setting_key, "setting_value": s.setting_value, "descricao": s.descricao} for s in settings_list]

@app.get("/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
