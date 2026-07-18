# app/schemas/aviso.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class AvisoBase(BaseModel):
    titulo: str
    texto: Optional[str] = None
    midia_url: Optional[str] = None
    midia_tipo: Optional[str] = None
    link_url: Optional[str] = None
    link_texto: Optional[str] = None
    ativo: bool = True
    programado_inicio: Optional[datetime] = None
    programado_fim: Optional[datetime] = None

class AvisoCreate(AvisoBase):
    pass

class AvisoUpdate(BaseModel):
    titulo: Optional[str] = None
    texto: Optional[str] = None
    midia_url: Optional[str] = None
    midia_tipo: Optional[str] = None
    link_url: Optional[str] = None
    link_texto: Optional[str] = None
    ativo: Optional[bool] = None
    programado_inicio: Optional[datetime] = None
    programado_fim: Optional[datetime] = None

class AvisoResponse(AvisoBase):
    id: int
    data_cadastro: datetime

    class Config:
        from_attributes = True
