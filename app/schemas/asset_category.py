
from pydantic import BaseModel, ConfigDict


class AssetCategoryCreate(BaseModel):
    nome: str
    descricao: str | None = None


class AssetCategoryUpdate(BaseModel):
    nome: str | None = None
    descricao: str | None = None


class AssetCategoryResponse(BaseModel):
    id: int
    nome: str
    descricao: str | None = None

    model_config = ConfigDict(from_attributes=True)
