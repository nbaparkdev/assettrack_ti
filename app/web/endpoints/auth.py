
# app/web/endpoints/auth.py
from typing import Annotated
from fastapi import APIRouter, Request, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta

from app.database import get_db
from app.crud import user as user_crud
from app.api.v1.endpoints.auth import create_access_token
from app.config import settings

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login", response_class=HTMLResponse)
async def login_submit(
    request: Request,
    email: Annotated[str, Form()],
    password: Annotated[str, Form()],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    user = await user_crud.user.get_by_email(db, email=email)
    if not user or not user_crud.user.verify_password(password, user.hashed_password):
        # Retorna template com erro
        return templates.TemplateResponse("login.html", {"request": request, "error": "Email ou senha incorretos."})
    
    # Check if user is active (approved by admin)
    if not user.is_active:
        return templates.TemplateResponse("login.html", {
            "request": request, 
            "error": "Sua conta ainda não foi aprovada por um administrador. Aguarde a liberação do acesso."
        })
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role.value},
        expires_delta=access_token_expires
    )
    
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    return response



@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/register", response_class=HTMLResponse)
async def register_submit(
    request: Request,
    nome: Annotated[str, Form()],
    email: Annotated[str, Form()],
    password: Annotated[str, Form()],
    matricula: Annotated[str, Form()] = None,
    cargo: Annotated[str, Form()] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
):
    # Check if user exists
    user = await user_crud.user.get_by_email(db, email=email)
    if user:
        return templates.TemplateResponse("register.html", {"request": request, "error": "Email já cadastrado."})

    try:
        from app.schemas.user import UserCreate
        user_in = UserCreate(
            nome=nome,
            email=email,
            password=password,
            matricula=matricula,
            cargo=cargo
        )
        await user_crud.user.create(db, obj_in=user_in)
        # Login automatically or redirect to login? Let's redirect to login.
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    except Exception as e:
        return templates.TemplateResponse("register.html", {"request": request, "error": f"Erro ao cadastrar: {str(e)}"})

@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("access_token")
    return response
