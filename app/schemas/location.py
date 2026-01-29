
# app/schemas/location.py
from pydantic import BaseModel, ConfigDict
from typing import Optional

# ----- Departamento -----
class DepartamentoBase(BaseModel):
    nome: str
    responsavel_id: Optional[int] = None

class DepartamentoCreate(DepartamentoBase):
    pass

class DepartamentoUpdate(DepartamentoBase):
    nome: Optional[str] = None

class Departamento(DepartamentoBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# ----- Localizacao -----
class LocalizacaoBase(BaseModel):
    nome: str
    departamento_id: Optional[int] = None

class LocalizacaoCreate(LocalizacaoBase):
    pass

class LocalizacaoUpdate(LocalizacaoBase):
    nome: Optional[str] = None

class Localizacao(LocalizacaoBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# ----- Armazenamento -----
class ArmazenamentoBase(BaseModel):
    nome: str
    capacidade_max: Optional[int] = 0
    tipo_itens: Optional[str] = None

class ArmazenamentoCreate(ArmazenamentoBase):
    pass

class ArmazenamentoUpdate(ArmazenamentoBase):
    nome: Optional[str] = None

class Armazenamento(ArmazenamentoBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
