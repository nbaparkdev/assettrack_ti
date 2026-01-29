
# app/schemas/asset.py
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal
from app.models.asset import AssetStatus
from app.schemas.location import Departamento, Localizacao, Armazenamento
from app.schemas.user import UserResponse

class AssetBase(BaseModel):
    nome: str
    serial_number: str
    modelo: Optional[str] = None
    data_aquisicao: Optional[datetime] = None
    valor: Optional[Decimal] = None
    status: AssetStatus = AssetStatus.DISPONIVEL
    qr_code_path: Optional[str] = None
    foto_path: Optional[str] = None
    
    current_user_id: Optional[int] = None
    current_departamento_id: Optional[int] = None
    current_local_id: Optional[int] = None
    current_armazenamento_id: Optional[int] = None

class AssetCreate(AssetBase):
    pass

class AssetUpdate(BaseModel):
    nome: Optional[str] = None
    serial_number: Optional[str] = None
    modelo: Optional[str] = None
    data_aquisicao: Optional[datetime] = None
    valor: Optional[Decimal] = None
    status: Optional[AssetStatus] = None
    
    current_user_id: Optional[int] = None
    current_departamento_id: Optional[int] = None
    current_local_id: Optional[int] = None
    current_armazenamento_id: Optional[int] = None

class AssetResponse(AssetBase):
    id: int
    current_user: Optional[UserResponse] = None
    current_departamento: Optional[Departamento] = None
    current_local: Optional[Localizacao] = None
    current_armazenamento: Optional[Armazenamento] = None

    model_config = ConfigDict(from_attributes=True)
