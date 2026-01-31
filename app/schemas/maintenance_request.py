
# app/schemas/maintenance_request.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from app.models.maintenance_request import PrioridadeSolicitacao, StatusSolicitacaoManutencao


class SolicitacaoManutencaoBase(BaseModel):
    asset_id: int
    descricao: str = Field(..., min_length=10, max_length=2000)
    prioridade: PrioridadeSolicitacao = PrioridadeSolicitacao.MEDIA


class SolicitacaoManutencaoCreate(SolicitacaoManutencaoBase):
    pass


class SolicitacaoManutencaoUpdate(BaseModel):
    status: Optional[StatusSolicitacaoManutencao] = None
    observacao_resposta: Optional[str] = None


class SolicitacaoManutencaoResponse(SolicitacaoManutencaoBase):
    id: int
    solicitante_id: int
    status: StatusSolicitacaoManutencao
    data_solicitacao: datetime
    data_resposta: Optional[datetime] = None
    responsavel_id: Optional[int] = None
    observacao_resposta: Optional[str] = None
    manutencao_id: Optional[int] = None
    
    # Nested info (populated in endpoint)
    solicitante_nome: Optional[str] = None
    asset_nome: Optional[str] = None
    asset_serial: Optional[str] = None
    responsavel_nome: Optional[str] = None

    class Config:
        from_attributes = True
