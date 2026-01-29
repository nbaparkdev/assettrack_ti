
# app/schemas/transaction.py
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from app.models.transaction import TipoMovimentacao, StatusSolicitacao
from app.schemas.user import UserResponse
from app.schemas.asset import AssetResponse

# ----- Movimentacao -----
class MovimentacaoBase(BaseModel):
    asset_id: int
    tipo: TipoMovimentacao
    de_user_id: Optional[int] = None
    para_user_id: Optional[int] = None
    de_departamento_id: Optional[int] = None
    para_departamento_id: Optional[int] = None
    observacao: Optional[str] = None

class MovimentacaoCreate(MovimentacaoBase):
    pass

class MovimentacaoResponse(MovimentacaoBase):
    id: int
    data: datetime
    de_user: Optional[UserResponse] = None
    para_user: Optional[UserResponse] = None
    asset: Optional[AssetResponse] = None

    model_config = ConfigDict(from_attributes=True)

# ----- Solicitacao -----
class SolicitacaoBase(BaseModel):
    asset_id: Optional[int] = None
    motivo: str
    data_prevista_devolucao: Optional[datetime] = None

class SolicitacaoCreate(SolicitacaoBase):
    pass

class SolicitacaoUpdate(BaseModel):
    status: Optional[StatusSolicitacao] = None
    aprovador_id: Optional[int] = None
    data_aprovacao: Optional[datetime] = None

class SolicitacaoResponse(SolicitacaoBase):
    id: int
    solicitante_id: int
    status: StatusSolicitacao
    data_solicitacao: datetime
    
    aprovador_id: Optional[int] = None
    data_aprovacao: Optional[datetime] = None
    
    solicitante: Optional[UserResponse] = None
    aprovador: Optional[UserResponse] = None
    asset: Optional[AssetResponse] = None

    model_config = ConfigDict(from_attributes=True)
