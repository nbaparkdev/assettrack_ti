
# app/schemas/maintenance_request.py
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.maintenance_request import (
    PrioridadeSolicitacao,
    StatusSolicitacaoManutencao,
)


class SolicitacaoManutencaoBase(BaseModel):
    asset_id: int
    descricao: str = Field(..., min_length=10, max_length=2000)
    prioridade: PrioridadeSolicitacao = PrioridadeSolicitacao.MEDIA


class SolicitacaoManutencaoCreate(SolicitacaoManutencaoBase):
    pass


class SolicitacaoManutencaoUpdate(BaseModel):
    status: StatusSolicitacaoManutencao | None = None
    observacao_resposta: str | None = None


class SolicitacaoManutencaoResponse(SolicitacaoManutencaoBase):
    id: int
    solicitante_id: int
    status: StatusSolicitacaoManutencao
    data_solicitacao: datetime
    data_resposta: datetime | None = None
    responsavel_id: int | None = None
    observacao_resposta: str | None = None
    manutencao_id: int | None = None
    
    # Nested info (populated in endpoint)
    solicitante_nome: str | None = None
    asset_nome: str | None = None
    asset_serial: str | None = None
    responsavel_nome: str | None = None

    class Config:
        from_attributes = True
