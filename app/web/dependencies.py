
# app/web/dependencies.py
from typing import Annotated, Optional
from fastapi import Request, Depends, HTTPException, status, Cookie
from fastapi.responses import RedirectResponse
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.config import settings
from app.crud import user as user_crud
from app.models.user import User
from app.schemas.user import TokenData

async def get_current_user_from_cookie(
    request: Request,
    access_token: Optional[str] = Cookie(None),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    # Tentativa de pegar do cookie. O cookie vem como "Bearer <token>" ou só "<token>" dependendo de como salvamos.
    # No auth.py salvamos como "Bearer <token>"?
    # response.set_cookie(key="access_token", value=f"Bearer {access_token}"...)
    
    token = access_token
    if not token:
        return None
        
    if token.startswith("Bearer "):
        token = token.split(" ")[1]

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
        token_data = TokenData(email=email)
    except JWTError:
        return None
        
    user = await user_crud.user.get_by_email(db, email=token_data.email)
    return user

async def get_active_user_web(
    request: Request,
    user: Annotated[Optional[User], Depends(get_current_user_from_cookie)]
) -> User:
    if not user:
        raise HTTPException(status_code=status.HTTP_302_FOUND, headers={"Location": "/login"})
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return user
