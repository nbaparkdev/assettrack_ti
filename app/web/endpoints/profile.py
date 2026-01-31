from typing import Annotated, Optional
from fastapi import APIRouter, Request, Depends, HTTPException, Form, UploadFile, File, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import shutil
import os
import uuid
from pathlib import Path

from app.database import get_db
from app.web.dependencies import get_active_user_web
from app.models.user import User
from app.models.location import Departamento
from app.crud import user as user_crud

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

UPLOAD_DIR = Path("static/img/avatars")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

@router.get("", response_class=HTMLResponse)
async def profile_page(
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    # Fetch user again to ensure fresh data
    user_refreshed = await db.get(User, current_user.id)
    if not user_refreshed:
        # Should ensure user is logged out if not found?
        pass

    # Fetch departments for the dropdown
    result = await db.execute(select(Departamento).order_by(Departamento.nome))
    departamentos = result.scalars().all()

    return templates.TemplateResponse("profile.html", {
        "request": request,
        "user": user_refreshed,
        "departamentos": departamentos,
        "title": "Meu Perfil"
    })

@router.post("/update")
async def update_profile(
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)],
    nome: str = Form(...),
    cargo: str = Form(None),
    departamento_id: Optional[str] = Form(None),
    avatar: UploadFile = File(None)
):
    user_db = await db.get(User, current_user.id)
    if not user_db:
         raise HTTPException(status_code=404, detail="Usuário não encontrado")

    # Update text fields
    user_db.nome = nome
    user_db.cargo = cargo
    
    # Handle departamento_id (empty string -> None)
    if departamento_id and departamento_id.isdigit():
        user_db.departamento_id = int(departamento_id)
    else:
        user_db.departamento_id = None

    # Handle Avatar Upload
    if avatar and avatar.filename:
        # Generate unique filename
        ext = os.path.splitext(avatar.filename)[1]
        filename = f"user_{user_db.id}_{uuid.uuid4().hex[:8]}{ext}"
        file_path = UPLOAD_DIR / filename
        
        try:
            with file_path.open("wb") as buffer:
                shutil.copyfileobj(avatar.file, buffer)
            
            # Remove old avatar if exists (optional but good for cleanup)
            # if user_db.avatar_url: ...
            
            # Update DB path (store relative to static or full url? usually relative)
            user_db.avatar_url = f"/static/img/avatars/{filename}"
        except Exception as e:
            print(f"Error saving file: {e}")
            # Could return error to user

    await db.commit()
    await db.refresh(user_db)
    
    return RedirectResponse(url="/profile", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/password")
async def change_password(
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...)
):
    # Basic validation
    if new_password != confirm_password:
         return templates.TemplateResponse("profile.html", {
            "request": request,
            "user": current_user,
            "error_password": "As senhas não coincidem.",
            "active_tab": "security" # To reopen security tab if implementing tabs
        })

    user_db = await db.get(User, current_user.id)
    
    # Verify old password
    if not user_crud.user.verify_password(current_password, user_db.hashed_password):
         return templates.TemplateResponse("profile.html", {
            "request": request,
            "user": current_user,
            "error_password": "Senha atual incorreta.",
            "active_tab": "security"
        })

    # Update password
    user_db.hashed_password = user_crud.user.get_password_hash(new_password)
    await db.commit()

    return RedirectResponse(url="/profile?success=password_updated", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/qr/generate")
async def generate_qr_token_endpoint(
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Gera um novo token QR Code para o usuário logado"""
    await user_crud.user.regenerate_qr_token(db, user_id=current_user.id)
    return RedirectResponse(url="/profile", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/pin")
async def update_pin(
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)],
    pin: str = Form(...),
    confirm_pin: str = Form(...)
):
    """Atualiza o PIN de acesso do usuário"""
    if pin != confirm_pin:
        return templates.TemplateResponse("profile.html", {
            "request": request,
            "user": current_user,
            "error_pin": "Os PINs não coincidem.",
            "active_tab": "security"
        })
    
    if len(pin) < 4 or len(pin) > 6 or not pin.isdigit():
         return templates.TemplateResponse("profile.html", {
            "request": request,
            "user": current_user,
            "error_pin": "O PIN deve ter entre 4 e 6 dígitos numéricos.",
            "active_tab": "security"
        })

    try:
        await user_crud.user.set_pin(db, user_id=current_user.id, pin=pin)
    except ValueError as e:
         return templates.TemplateResponse("profile.html", {
            "request": request,
            "user": current_user,
            "error_pin": str(e),
            "active_tab": "security"
        })

    return RedirectResponse(url="/profile?success=pin_updated", status_code=status.HTTP_303_SEE_OTHER)
