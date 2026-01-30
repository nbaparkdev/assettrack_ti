
# app/web/endpoints/setores.py
from typing import Annotated
from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.web.dependencies import get_active_user_web
from app.models.user import User, UserRole
from app.models.location import Departamento
from app.database import get_db

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


async def check_manager_role(current_user: Annotated[User, Depends(get_active_user_web)]):
    """Verifica se o usuário é ADMIN ou GERENTE."""
    if current_user.role not in [UserRole.ADMIN, UserRole.GERENTE]:
        raise HTTPException(status_code=403, detail="Acesso negado. Somente Admin ou Gerente.")
    return current_user


@router.get("/", response_class=HTMLResponse)
async def list_setores(
    request: Request,
    current_user: Annotated[User, Depends(check_manager_role)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    result = await db.execute(select(Departamento).order_by(Departamento.nome))
    setores = result.scalars().all()
    
    return templates.TemplateResponse("setores/list.html", {
        "request": request,
        "user": current_user,
        "setores": setores,
        "title": "Gerenciar Setores"
    })


@router.post("/new", response_class=HTMLResponse)
async def create_setor(
    request: Request,
    nome: Annotated[str, Form()],
    current_user: Annotated[User, Depends(check_manager_role)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    # Check for existing setor with same name
    result = await db.execute(select(Departamento).filter(Departamento.nome == nome))
    existing = result.scalars().first()
    if existing:
        # Re-render the list with an error message
        result = await db.execute(select(Departamento).order_by(Departamento.nome))
        setores = result.scalars().all()
        return templates.TemplateResponse("setores/list.html", {
            "request": request,
            "user": current_user,
            "setores": setores,
            "error": f"Setor '{nome}' já existe.",
            "title": "Gerenciar Setores"
        })
    
    new_setor = Departamento(nome=nome)
    db.add(new_setor)
    await db.commit()
    
    return RedirectResponse(url="/setores", status_code=303)


@router.post("/{setor_id}/delete", response_class=HTMLResponse)
async def delete_setor(
    request: Request,
    setor_id: int,
    current_user: Annotated[User, Depends(check_manager_role)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    setor = await db.get(Departamento, setor_id)
    if setor:
        await db.delete(setor)
        await db.commit()
    
    return RedirectResponse(url="/setores", status_code=303)
