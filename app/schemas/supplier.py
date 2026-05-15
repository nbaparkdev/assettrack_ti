# app/schemas/supplier.py
from pydantic import BaseModel, ConfigDict
from typing import Optional, List

class FornecedorBase(BaseModel):
    nome: str
    razao_social: Optional[str] = None
    cnpj: Optional[str] = None
    email: Optional[str] = None
    telefone: Optional[str] = None
    endereco: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    tipo_fornecedor: Optional[str] = None

class FornecedorCreate(FornecedorBase):
    pass

class FornecedorUpdate(BaseModel):
    nome: Optional[str] = None
    razao_social: Optional[str] = None
    cnpj: Optional[str] = None
    email: Optional[str] = None
    telefone: Optional[str] = None
    endereco: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    tipo_fornecedor: Optional[str] = None

class FornecedorResponse(FornecedorBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
