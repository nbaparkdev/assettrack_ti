# app/web/endpoints/users.py
from typing import Annotated
from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.web.dependencies import get_active_user_web
from app.models.user import User, UserRole

router = APIRouter(prefix="/admin/users", tags=["admin-users"])
templates = Jinja2Templates(directory="app/templates")

# Dependency to check admin/manager role
async def require_admin(current_user: Annotated[User, Depends(get_active_user_web)]):
    if str(current_user.role.value).lower() not in ["admin", "gerente_ti", "gerente_infra"]:
        raise HTTPException(status_code=403, detail="Acesso negado")
    return current_user

@router.get("", response_class=HTMLResponse)
async def list_users(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)]
):
    """List all users for admin management"""
    result = await db.execute(select(User).order_by(User.nome))
    users = result.scalars().all()
    
    return templates.TemplateResponse("users.html", {
        "request": request,
        "user": admin,
        "users": users,
        "title": "Gerenciar Usuários",
        "roles": UserRole
    })

@router.get("/{user_id}/edit", response_class=HTMLResponse)
async def edit_user_form(
    user_id: int,
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)]
):
    """Show edit form for a user"""
    target_user = await db.get(User, user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    return templates.TemplateResponse("user_edit.html", {
        "request": request,
        "user": admin,
        "target_user": target_user,
        "title": f"Editar {target_user.nome}",
        "roles": UserRole
    })

@router.post("/{user_id}/edit")
async def update_user(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
    nome: str = Form(...),
    email: str = Form(...),
    matricula: str = Form(None),
    cargo: str = Form(None),
    role: str = Form(...),
    is_active: bool = Form(False)
):
    """Update user data"""
    target_user = await db.get(User, user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    # Update fields
    target_user.nome = nome
    target_user.email = email
    target_user.matricula = matricula if matricula else None
    target_user.cargo = cargo if cargo else None
    target_user.role = UserRole(role)
    target_user.is_active = is_active
    
    from app.core.errors import get_friendly_db_error
    try:
        await db.commit()
        return RedirectResponse(url="/admin/users", status_code=303)
    except Exception as e:
        await db.rollback()
        return templates.TemplateResponse("user_edit.html", {
            "request": request,
            "user": admin,
            "target_user": target_user,
            "title": f"Editar {target_user.nome}",
            "roles": UserRole,
            "error": get_friendly_db_error(e)
        })

@router.post("/{user_id}/approve")
async def approve_user(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)]
):
    """Approve (activate) a user"""
    target_user = await db.get(User, user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    target_user.is_active = True
    await db.commit()
    return RedirectResponse(url="/admin/users", status_code=303)

@router.post("/{user_id}/delete")
async def delete_user(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)]
):
    """Delete a user"""
    target_user = await db.get(User, user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    # Prevent self-deletion
    if target_user.id == admin.id:
        raise HTTPException(status_code=400, detail="Você não pode excluir a si mesmo")
    
    from sqlalchemy.exc import IntegrityError
    try:
        await db.delete(target_user)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=400,
            detail="Não é possível excluir este usuário pois ele possui registros vinculados (como Centro de Custo, Ativos ou Chamados)."
        )
    return RedirectResponse(url="/admin/users", status_code=303)

@router.post("/{user_id}/reset-password")
async def reset_password(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    admin: Annotated[User, Depends(require_admin)],
    new_password: str = Form(...)
):
    """Admin resets a user's password"""
    from app.crud.user import user as user_crud
    
    target_user = await db.get(User, user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    target_user.hashed_password = user_crud.get_password_hash(new_password)
    await db.commit()
    
    # Return to the edit page with a success message (or just redirect back to users list)
    return RedirectResponse(url=f"/admin/users/{user_id}/edit?msg=Senha+redefinida+com+sucesso", status_code=303)
