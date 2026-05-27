from pydantic import BaseModel, ConfigDict
from typing import Optional


class AssetCategoryCreate(BaseModel):
    nome: str
    descricao: Optional[str] = None


class AssetCategoryUpdate(BaseModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None


class AssetCategoryResponse(BaseModel):
    id: int
    nome: str
    descricao: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
