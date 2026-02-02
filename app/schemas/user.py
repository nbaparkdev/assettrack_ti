
# app/schemas/user.py
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List
from datetime import datetime
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

# === QR Code Schemas ===

class UserQRResponse(BaseModel):
    """Resposta com QR Code do usuário"""
    qr_code_base64: str
    qr_token: str
    created_at: Optional[datetime] = None
    has_pin: bool = False

class UserBadgeResponse(BaseModel):
    """Dados para crachá digital"""
    id: int
    nome: str
    email: str
    matricula: Optional[str] = None
    cargo: Optional[str] = None
    departamento_nome: Optional[str] = None
    avatar_url: Optional[str] = None
    qr_code_base64: str
    
    model_config = ConfigDict(from_attributes=True)

class PINSetupRequest(BaseModel):
    """Request para configurar PIN"""
    pin: str  # 4-6 dígitos

class QRLoginRequest(BaseModel):
    """Request para login via QR Code"""
    qr_token: str
    pin: str

class PendingDeliveryItem(BaseModel):
    id: int
    tipo: str  # "solicitacao" ou "manutencao"
    asset_tag: str
    asset_nome: str
    data_solicitacao: datetime
    status: str

class UserPublicProfile(BaseModel):
    """Perfil público do usuário (visível após scan do QR)"""
    id: int
    nome: str
    email: str
    matricula: Optional[str] = None
    cargo: Optional[str] = None
    departamento_nome: Optional[str] = None
    avatar_url: Optional[str] = None
    
    pending_deliveries: List[PendingDeliveryItem] = []
    
    model_config = ConfigDict(from_attributes=True)

class DeliveryConfirmRequest(BaseModel):
    """Request para confirmar entrega via QR"""
    qr_token: Optional[str] = None  # Opcional: Admin/Gerente podem confirmar sem QR
    solicitacao_id: Optional[int] = None
    manutencao_id: Optional[int] = None
    observacao: Optional[str] = None

