
# app/main.py
import uvicorn
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from app.config import settings
from app.api.v1 import api_router
from app.database import engine, Base
from app.web import web_router
from app.web.endpoints import admin 
from app.core.rate_limit import limiter
from slowapi.errors import RateLimitExceeded

# Função para criar tabelas no startup (apenas para dev rápido se não usar alembic)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all) # CUIDADO: Limpa banco
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    await engine.dispose()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

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

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates instantiation (global access if needed, or per file)
templates = Jinja2Templates(directory="app/templates")

app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(web_router)

@app.get("/health")
def health_check():
    return {"status": "ok"}

# O root "/" será servido pelo web.router depois

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
