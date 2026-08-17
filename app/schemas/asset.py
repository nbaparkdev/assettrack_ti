
# app/schemas/asset.py
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models.asset import AssetStatus
from app.schemas.asset_category import AssetCategoryResponse
from app.schemas.location import Armazenamento, Departamento, Localizacao
from app.schemas.user import UserResponse


class AssetBase(BaseModel):
    nome: str
    e_patrimonio: str
    modelo: str | None = None
    descricao: str | None = None
    data_aquisicao: datetime | None = None
    valor: Decimal | None = None
    status: AssetStatus = AssetStatus.DISPONIVEL
    qr_code_path: str | None = None
    foto_path: str | None = None
    numero_serie: str | None = None
    em_posse_de: str | None = None
    bloqueado: bool = False
    requer_termo_rh: bool = False

    categoria_id: int | None = None
    created_by_id: int | None = None
    fornecedor_id: int | None = None
    nota_fiscal_id: int | None = None

    current_user_id: int | None = None
    current_departamento_id: int | None = None
    current_local_id: int | None = None
    current_armazenamento_id: int | None = None

class AssetCreate(AssetBase):
    pass

class AssetUpdate(BaseModel):
    nome: str | None = None
    e_patrimonio: str | None = None
    modelo: str | None = None
    descricao: str | None = None
    data_aquisicao: datetime | None = None
    valor: Decimal | None = None
    status: AssetStatus | None = None
    numero_serie: str | None = None
    em_posse_de: str | None = None
    bloqueado: bool | None = None
    requer_termo_rh: bool | None = None
    fornecedor_id: int | None = None
    nota_fiscal_id: int | None = None
    foto_path: str | None = None
    categoria_id: int | None = None

    current_user_id: int | None = None
    current_departamento_id: int | None = None
    current_local_id: int | None = None
    current_armazenamento_id: int | None = None

class AssetResponse(AssetBase):
    id: int
    current_user: UserResponse | None = None
    current_departamento: Departamento | None = None
    current_local: Localizacao | None = None
    current_armazenamento: Armazenamento | None = None
    categoria: AssetCategoryResponse | None = None

    model_config = ConfigDict(from_attributes=True)
