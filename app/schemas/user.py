
# app/schemas/user.py
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr

from app.models.user import UserRole
from app.schemas.location import Departamento


class UserBase(BaseModel):
    email: EmailStr
    nome: str
    matricula: str | None = None
    cargo: str | None = None
    role: UserRole = UserRole.USUARIO
    is_active: bool = False
    departamento_id: int | None = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    email: EmailStr | None = None
    nome: str | None = None
    matricula: str | None = None
    cargo: str | None = None
    role: UserRole | None = None
    is_active: bool | None = None
    departamento_id: int | None = None
    password: str | None = None

class UserResponse(UserBase):
    id: int
    departamento: Departamento | None = None
    
    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: str | None = None
    role: UserRole | None = None

# === QR Code Schemas ===

class UserQRResponse(BaseModel):
    """Resposta com QR Code do usuário"""
    qr_code_base64: str
    qr_token: str
    created_at: datetime | None = None
    has_pin: bool = False

class UserBadgeResponse(BaseModel):
    """Dados para crachá digital"""
    id: int
    nome: str
    email: str
    matricula: str | None = None
    cargo: str | None = None
    departamento_nome: str | None = None
    avatar_url: str | None = None
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
    matricula: str | None = None
    cargo: str | None = None
    departamento_nome: str | None = None
    avatar_url: str | None = None
    
    pending_deliveries: list[PendingDeliveryItem] = []
    
    model_config = ConfigDict(from_attributes=True)

class DeliveryConfirmRequest(BaseModel):
    """Request para confirmar entrega via QR"""
    qr_token: str | None = None  # Opcional: Admin/Gerente podem confirmar sem QR
    solicitacao_id: int | None = None
    manutencao_id: int | None = None
    observacao: str | None = None

