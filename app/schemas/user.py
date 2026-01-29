
# app/schemas/user.py
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from app.models.user import UserRole
from app.schemas.location import Departamento

class UserBase(BaseModel):
    email: EmailStr
    nome: str
    matricula: Optional[str] = None
    cargo: Optional[str] = None
    role: UserRole = UserRole.USUARIO
    is_active: bool = False
    departamento_id: Optional[int] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    nome: Optional[str] = None
    matricula: Optional[str] = None
    cargo: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    departamento_id: Optional[int] = None
    password: Optional[str] = None

class UserResponse(UserBase):
    id: int
    departamento: Optional[Departamento] = None
    
    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[UserRole] = None
