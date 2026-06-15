
# app/schemas/asset.py
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal
from app.models.asset import AssetStatus
from app.schemas.location import Departamento, Localizacao, Armazenamento
from app.schemas.user import UserResponse

from app.schemas.asset_category import AssetCategoryResponse

class AssetBase(BaseModel):
    nome: str
    e_patrimonio: str
    modelo: Optional[str] = None
    descricao: Optional[str] = None
    data_aquisicao: Optional[datetime] = None
    valor: Optional[Decimal] = None
    status: AssetStatus = AssetStatus.DISPONIVEL
    qr_code_path: Optional[str] = None
    foto_path: Optional[str] = None
    numero_serie: Optional[str] = None
    em_posse_de: Optional[str] = None

    categoria_id: Optional[int] = None
    created_by_id: Optional[int] = None
    fornecedor_id: Optional[int] = None
    nota_fiscal_id: Optional[int] = None

    current_user_id: Optional[int] = None
    current_departamento_id: Optional[int] = None
    current_local_id: Optional[int] = None
    current_armazenamento_id: Optional[int] = None

class AssetCreate(AssetBase):
    pass

class AssetUpdate(BaseModel):
    nome: Optional[str] = None
    e_patrimonio: Optional[str] = None
    modelo: Optional[str] = None
    descricao: Optional[str] = None
    data_aquisicao: Optional[datetime] = None
    valor: Optional[Decimal] = None
    status: Optional[AssetStatus] = None
    numero_serie: Optional[str] = None
    em_posse_de: Optional[str] = None
    fornecedor_id: Optional[int] = None
    nota_fiscal_id: Optional[int] = None
    foto_path: Optional[str] = None
    categoria_id: Optional[int] = None

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
    categoria: Optional[AssetCategoryResponse] = None

    model_config = ConfigDict(from_attributes=True)
