
# app/schemas/location.py

from pydantic import BaseModel, ConfigDict


# ----- Departamento -----
class DepartamentoBase(BaseModel):
    nome: str
    responsavel_id: int | None = None

class DepartamentoCreate(DepartamentoBase):
    pass

class DepartamentoUpdate(DepartamentoBase):
    nome: str | None = None

class Departamento(DepartamentoBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# ----- Localizacao -----
class LocalizacaoBase(BaseModel):
    nome: str
    departamento_id: int | None = None

class LocalizacaoCreate(LocalizacaoBase):
    pass

class LocalizacaoUpdate(LocalizacaoBase):
    nome: str | None = None

class Localizacao(LocalizacaoBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# ----- Armazenamento -----
class ArmazenamentoBase(BaseModel):
    nome: str
    capacidade_max: int | None = 0
    tipo_itens: str | None = None

class ArmazenamentoCreate(ArmazenamentoBase):
    pass

class ArmazenamentoUpdate(ArmazenamentoBase):
    nome: str | None = None

class Armazenamento(ArmazenamentoBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
