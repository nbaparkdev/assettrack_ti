
# app/api/v1/endpoints/users.py
from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import dependencies
from app.crud import user as user_crud
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.database import get_db

router = APIRouter()

@router.get("/", response_model=List[UserResponse])
async def read_users(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dependencies.User, Depends(dependencies.get_current_active_manager_or_superuser)],
    skip: int = 0,
    limit: int = 100,
):
    users = await user_crud.user.get_multi(db, skip=skip, limit=limit)
    return users

@router.post("/", response_model=UserResponse)
async def create_user_by_admin(
    user_in: UserCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dependencies.User, Depends(dependencies.get_current_active_superuser)],
):
    user = await user_crud.user.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )
    user = await user_crud.user.create(db, obj_in=user_in)
    return user

@router.get("/{user_id}", response_model=UserResponse)
async def read_user_by_id(
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dependencies.User, Depends(dependencies.get_current_active_user)],
):
    user = await user_crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # Se não for admin/gerente, só pode ver a si mesmo? 
    # Depende da regra. Vamos deixar aberto para usuários verem quem está com asset, mas editar é restrito.
    return user

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_in: UserUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dependencies.User, Depends(dependencies.get_current_active_superuser)],
):
    user = await user_crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user = await user_crud.user.update(db, db_obj=user, obj_in=user_in)
    return user
