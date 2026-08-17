
# app/schemas/transaction.py
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.transaction import StatusSolicitacao, TipoMovimentacao
from app.schemas.asset import AssetResponse
from app.schemas.user import UserResponse


# ----- Movimentacao -----
class MovimentacaoBase(BaseModel):
    asset_id: int
    tipo: TipoMovimentacao
    de_user_id: int | None = None
    para_user_id: int | None = None
    de_departamento_id: int | None = None
    para_departamento_id: int | None = None
    observacao: str | None = None

class MovimentacaoCreate(MovimentacaoBase):
    pass

class MovimentacaoResponse(MovimentacaoBase):
    id: int
    data: datetime
    de_user: UserResponse | None = None
    para_user: UserResponse | None = None
    asset: AssetResponse | None = None

    model_config = ConfigDict(from_attributes=True)

# ----- Solicitacao -----
class SolicitacaoBase(BaseModel):
    asset_id: int | None = None
    motivo: str
    data_prevista_devolucao: datetime | None = None

class SolicitacaoCreate(SolicitacaoBase):
    pass

class SolicitacaoUpdate(BaseModel):
    status: StatusSolicitacao | None = None
    aprovador_id: int | None = None
    data_aprovacao: datetime | None = None

class SolicitacaoResponse(SolicitacaoBase):
    id: int
    solicitante_id: int
    status: StatusSolicitacao
    data_solicitacao: datetime
    
    aprovador_id: int | None = None
    data_aprovacao: datetime | None = None
    
    solicitante: UserResponse | None = None
    aprovador: UserResponse | None = None
    asset: AssetResponse | None = None

    model_config = ConfigDict(from_attributes=True)
