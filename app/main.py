
# app/main.py
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
from app.config import settings
from app.api.v1 import api_router
from app.database import engine, Base
from app.web import web_router
from app.web.endpoints import admin 

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
