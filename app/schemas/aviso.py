# app/schemas/aviso.py
from datetime import datetime

from pydantic import BaseModel


class AvisoBase(BaseModel):
    titulo: str
    texto: str | None = None
    midia_url: str | None = None
    midia_tipo: str | None = None
    link_url: str | None = None
    link_texto: str | None = None
    ativo: bool = True
    programado_inicio: datetime | None = None
    programado_fim: datetime | None = None

class AvisoCreate(AvisoBase):
    pass

class AvisoUpdate(BaseModel):
    titulo: str | None = None
    texto: str | None = None
    midia_url: str | None = None
    midia_tipo: str | None = None
    link_url: str | None = None
    link_texto: str | None = None
    ativo: bool | None = None
    programado_inicio: datetime | None = None
    programado_fim: datetime | None = None

class AvisoResponse(AvisoBase):
    id: int
    data_cadastro: datetime

    class Config:
        from_attributes = True
