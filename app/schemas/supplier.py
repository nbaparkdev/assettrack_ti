# app/schemas/supplier.py

from pydantic import BaseModel, ConfigDict


class FornecedorBase(BaseModel):
    nome: str
    razao_social: str | None = None
    cnpj: str | None = None
    email: str | None = None
    telefone: str | None = None
    endereco: str | None = None
    cidade: str | None = None
    estado: str | None = None
    tipo_fornecedor: str | None = None

class FornecedorCreate(FornecedorBase):
    pass

class FornecedorUpdate(BaseModel):
    nome: str | None = None
    razao_social: str | None = None
    cnpj: str | None = None
    email: str | None = None
    telefone: str | None = None
    endereco: str | None = None
    cidade: str | None = None
    estado: str | None = None
    tipo_fornecedor: str | None = None

class FornecedorResponse(FornecedorBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
