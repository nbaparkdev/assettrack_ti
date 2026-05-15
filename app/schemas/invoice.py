# app/schemas/invoice.py
from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.schemas.supplier import FornecedorResponse

class NotaFiscalBase(BaseModel):
    numero_nota: str
    fornecedor_id: int
    xml_path: Optional[str] = None
    data_emissao: Optional[datetime] = None
    valor_total: Optional[float] = None
    natureza_operacao: Optional[str] = None
    emitente_nome: Optional[str] = None
    emitente_cnpj: Optional[str] = None
    destinatario_nome: Optional[str] = None
    destinatario_cnpj: Optional[str] = None
    itens: Optional[List[Dict[str, Any]]] = None

class NotaFiscalCreate(NotaFiscalBase):
    pass

class NotaFiscalUpdate(BaseModel):
    numero_nota: Optional[str] = None
    fornecedor_id: Optional[int] = None
    xml_path: Optional[str] = None
    itens: Optional[List[Dict[str, Any]]] = None

class NotaFiscalResponse(NotaFiscalBase):
    id: int
    data_cadastro: datetime
    fornecedor: Optional[FornecedorResponse] = None
    
    model_config = ConfigDict(from_attributes=True)
