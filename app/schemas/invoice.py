# app/schemas/invoice.py
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.schemas.supplier import FornecedorResponse


class NotaFiscalBase(BaseModel):
    numero_nota: str
    fornecedor_id: int
    xml_path: str | None = None
    data_emissao: datetime | None = None
    valor_total: float | None = None
    natureza_operacao: str | None = None
    emitente_nome: str | None = None
    emitente_cnpj: str | None = None
    destinatario_nome: str | None = None
    destinatario_cnpj: str | None = None
    itens: list[dict[str, Any]] | None = None

class NotaFiscalCreate(NotaFiscalBase):
    pass

class NotaFiscalUpdate(BaseModel):
    numero_nota: str | None = None
    fornecedor_id: int | None = None
    xml_path: str | None = None
    itens: list[dict[str, Any]] | None = None

class NotaFiscalResponse(NotaFiscalBase):
    id: int
    data_cadastro: datetime
    fornecedor: FornecedorResponse | None = None
    
    model_config = ConfigDict(from_attributes=True)
