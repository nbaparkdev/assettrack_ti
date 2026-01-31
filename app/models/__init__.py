
# app/models/__init__.py
from app.models.user import User, UserRole
from app.models.location import Departamento, Localizacao, Armazenamento
from app.models.asset import Asset, AssetStatus
from app.models.transaction import Movimentacao, Solicitacao, TipoMovimentacao, StatusSolicitacao
from app.models.maintenance import Manutencao, TipoManutencao, StatusManutencao, DestinoManutencao
from app.models.maintenance_request import SolicitacaoManutencao, PrioridadeSolicitacao, StatusSolicitacaoManutencao
from app.models.qr_log import QRLog, QRLogAction
from app.database import Base

