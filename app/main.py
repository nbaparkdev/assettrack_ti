# app/main.py
import os
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
import app.models
from slowapi.errors import RateLimitExceeded

# Base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)

# Função para criar tabelas no startup
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    await engine.dispose()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# Templates instantiation
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Mount static files
if os.path.exists(os.path.join(PROJECT_ROOT, "static")):
    app.mount("/static", StaticFiles(directory=os.path.join(PROJECT_ROOT, "static")), name="static")

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

@app.get("/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
