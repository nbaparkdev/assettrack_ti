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
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.web.dependencies import get_current_user_from_cookie
from app.database import SessionLocal

# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

# Função para criar tabelas no startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup — cria tabelas
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Garantir que a coluna requer_termo_rh existe na tabela assets
    from sqlalchemy import text
    try:
        async with engine.begin() as conn:
            await conn.execute(text("ALTER TABLE assets ADD COLUMN requer_termo_rh BOOLEAN DEFAULT FALSE"))
    except Exception:
        # Fallback para SQLite antigo caso não reconheça FALSE (embora reconheça)
        try:
            async with engine.begin() as conn:
                await conn.execute(text("ALTER TABLE assets ADD COLUMN requer_termo_rh BOOLEAN DEFAULT 0"))
        except Exception:
            pass

    # Auto-migration: adicionar valores ao enum userrole no PostgreSQL
    # ALTER TYPE ADD VALUE não pode rodar dentro de uma transação.
    # Solução: asyncpg direto (já instalado como dependência).
    # Conexões asyncpg são autocommit por padrão fora de transação.
    # engine.url.password retorna a senha real (não mascarada como str(engine.url)).
    _logger = logging.getLogger("app.main")
    if "postgresql" in str(engine.url.drivername):
        try:
            import asyncpg as _asyncpg
            _url = engine.url
            _ac_conn = await _asyncpg.connect(
                host=_url.host,
                port=_url.port or 5432,
                user=_url.username,
                password=str(_url.password) if _url.password else None,
                database=_url.database,
            )
            try:
                for val in ['comprador', 'gerente_infra', 'rh']:
                    try:
                        exists = await _ac_conn.fetchval(
                            "SELECT 1 FROM pg_enum e "
                            "JOIN pg_type t ON e.enumtypid = t.oid "
                            "WHERE t.typname = 'userrole' AND e.enumlabel = $1",
                            val
                        )
                        if not exists:
                            await _ac_conn.execute(f"ALTER TYPE userrole ADD VALUE '{val}'")
                            _logger.info(f"✅ Enum userrole: adicionado valor '{val}'")
                        else:
                            _logger.info(f"Enum userrole: '{val}' já existe")
                    except Exception as e:
                        _logger.warning(f"⚠️ Enum userrole: falha ao adicionar '{val}': {e}")

                for val in ['Rascunho', 'Pendente', 'Aprovada', 'Reprovada']:
                    try:
                        exists = await _ac_conn.fetchval(
                            "SELECT 1 FROM pg_enum e "
                            "JOIN pg_type t ON e.enumtypid = t.oid "
                            "WHERE t.typname = 'purchaseresearchstatus' AND e.enumlabel = $1",
                            val
                        )
                        if not exists:
                            await _ac_conn.execute(f"ALTER TYPE purchaseresearchstatus ADD VALUE '{val}'")
                            _logger.info(f"✅ Enum purchaseresearchstatus: adicionado valor '{val}'")
                    except Exception as e:
                        pass
            finally:
                await _ac_conn.close()
        except Exception as e:
            _logger.warning(f"⚠️ Enum migration falhou: {e}")

    async with engine.begin() as conn:
        try:
            await conn.execute(text("ALTER TABLE purchase_research_items ADD COLUMN aprovado BOOLEAN DEFAULT TRUE"))
        except Exception:
            pass
        try:
            await conn.execute(text("ALTER TABLE purchase_research_items ADD COLUMN tipo_produto VARCHAR(20) DEFAULT 'Consumo'"))
        except Exception:
            pass
        try:
            await conn.execute(text("ALTER TABLE purchase_request_items ALTER COLUMN observacao TYPE TEXT"))
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




    # Manutenção Preventiva - Alterações de tabela para infra predial
    # Cada ALTER em transação separada: PostgreSQL aborta a transação inteira após qualquer erro
    async with engine.begin() as conn:
        try:
            await conn.execute(text("ALTER TABLE maintenance_orders ALTER COLUMN asset_id DROP NOT NULL"))
        except Exception:
            pass

    async with engine.begin() as conn:
        try:
            await conn.execute(text("ALTER TABLE maintenance_orders ADD COLUMN infra_predial_servico VARCHAR(255)"))
        except Exception:
            pass

    async with engine.begin() as conn:
        try:
            await conn.execute(text("ALTER TABLE maintenance_materials ADD COLUMN product_id INTEGER REFERENCES purchase_products(id)"))
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

        try:
            val_ai = await system_settings.get_setting(session, "ai_enabled", default_value="false")
            app.state.ai_enabled = (val_ai.lower() == "true")
        except Exception:
            app.state.ai_enabled = False

        try:
            val_adv = await system_settings.get_setting(session, "ai_advanced_functions", default_value="false")
            app.state.ai_advanced_functions = (val_adv.lower() == "true")
        except Exception:
            app.state.ai_advanced_functions = False

        try:
            import json
            perms_str = await system_settings.get_setting(session, "menu_permissions")
            if perms_str:
                app.state.menu_permissions = json.loads(perms_str)
            else:
                app.state.menu_permissions = {
                    "ativos": ["admin", "gerente_ti", "gerente_infra", "tecnico", "comprador", "usuario_comum"],
                    "fornecedores": ["admin", "gerente_ti", "gerente_infra", "comprador"],
                    "manutencao": ["admin", "gerente_ti", "gerente_infra", "tecnico"],
                    "tickets": ["admin", "gerente_ti", "gerente_infra", "tecnico", "comprador", "usuario_comum"],
                    "compras": ["admin", "gerente_ti", "gerente_infra", "comprador"],
                    "relatorios": ["admin", "gerente_ti", "gerente_infra", "comprador"],
                    "usuarios": ["admin", "gerente_ti", "gerente_infra"],
                    "backup": ["admin", "gerente_ti", "gerente_infra"]
                }
        except Exception:
            app.state.menu_permissions = {
                "ativos": ["admin", "gerente_ti", "gerente_infra", "tecnico", "comprador", "usuario_comum"],
                "fornecedores": ["admin", "gerente_ti", "gerente_infra", "comprador"],
                "manutencao": ["admin", "gerente_ti", "gerente_infra", "tecnico"],
                "tickets": ["admin", "gerente_ti", "gerente_infra", "tecnico", "comprador", "usuario_comum"],
                "compras": ["admin", "gerente_ti", "gerente_infra", "comprador"],
                "relatorios": ["admin", "gerente_ti", "gerente_infra", "comprador"],
                "usuarios": ["admin", "gerente_ti", "gerente_infra"],
                "backup": ["admin", "gerente_ti", "gerente_infra"]
            }

        # Debug: query and write users to a text file in the workspace.
        # Este bloco é apenas diagnóstico e nunca pode impedir o startup.
        try:
            from sqlalchemy import select
            from app.models.user import User
            res = await session.execute(select(User).order_by(User.id))
            users = res.scalars().all()
            import os
            debug_path = "/code/app/users_debug.txt" if os.path.exists("/code/app") else "app/users_debug.txt"
            with open(debug_path, "w") as f:
                f.write(f"TOTAL USERS IN DB: {len(users)}\n")
                for u in users:
                    role_str = u.role.value if hasattr(u.role, 'value') else str(u.role)
                    f.write(f"ID: {u.id} | Nome: {u.nome} | Email: {u.email} | Role: {role_str} | Is Active: {u.is_active} | Matricula: {u.matricula!r} | Cargo: {u.cargo!r}\n")
        except Exception as e:
            logging.getLogger("app.main").warning(f"Debug users_debug.txt falhou: {e}")

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
    request.state.ai_enabled = getattr(request.app.state, "ai_enabled", False)
    request.state.ai_advanced_functions = getattr(request.app.state, "ai_advanced_functions", False)
    request.state.menu_permissions = getattr(request.app.state, "menu_permissions", {
        "ativos": ["admin", "gerente_ti", "gerente_infra", "tecnico", "comprador", "usuario_comum"],
        "fornecedores": ["admin", "gerente_ti", "gerente_infra", "comprador"],
        "manutencao": ["admin", "gerente_ti", "gerente_infra", "tecnico"],
        "tickets": ["admin", "gerente_ti", "gerente_infra", "tecnico", "comprador", "usuario_comum"],
        "compras": ["admin", "gerente_ti", "gerente_infra", "comprador"],
        "relatorios": ["admin", "gerente_ti", "gerente_infra", "comprador"],
        "usuarios": ["admin", "gerente_ti", "gerente_infra"],
        "backup": ["admin", "gerente_ti", "gerente_infra"]
    })
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

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    is_api = (
        request.url.path.startswith("/api/") or 
        "application/json" in request.headers.get("accept", "").lower() or
        request.headers.get("x-requested-with") == "XMLHttpRequest"
    )

    if exc.status_code == 403:
        if is_api:
            return JSONResponse(
                status_code=403,
                content={"detail": exc.detail if exc.detail else "Acesso Negado."}
            )
        async with SessionLocal() as db:
            user = await get_current_user_from_cookie(request, access_token=request.cookies.get("access_token"), db=db)
        return templates.TemplateResponse("errors/403.html", {
            "request": request,
            "title": "Acesso Negado",
            "user": user,
            "detail": exc.detail if exc.detail and exc.detail != "Forbidden" else None
        }, status_code=403)

    elif exc.status_code == 404:
        if is_api:
            return JSONResponse(
                status_code=404,
                content={"detail": exc.detail if exc.detail else "Não encontrado."}
            )
        async with SessionLocal() as db:
            user = await get_current_user_from_cookie(request, access_token=request.cookies.get("access_token"), db=db)
        return templates.TemplateResponse("errors/404.html", {
            "request": request,
            "title": "Página não Encontrada",
            "user": user
        }, status_code=404)

    elif exc.status_code == 401:
        if is_api:
            return JSONResponse(
                status_code=401,
                content={"detail": exc.detail if exc.detail else "Não autorizado."}
            )
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/login", status_code=302)

    headers = getattr(exc, "headers", None)
    if exc.status_code in (301, 302, 303, 307, 308) and headers and "location" in {k.lower(): v for k, v in headers.items()}:
        from fastapi.responses import RedirectResponse
        # Reconstruct headers to preserve all of them, but let RedirectResponse handle the URL
        url = {k.lower(): v for k, v in headers.items()}["location"]
        return RedirectResponse(url=url, status_code=exc.status_code, headers=headers)

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=headers
    )

@app.exception_handler(500)
async def custom_500_handler(request: Request, exc):
    print(f"ERROR: {exc}") 
    async with SessionLocal() as db:
        user = await get_current_user_from_cookie(request, access_token=request.cookies.get("access_token"), db=db)
    return templates.TemplateResponse("errors/500.html", {
        "request": request,
        "title": "Erro Interno",
        "user": user
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
