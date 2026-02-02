
# app/models/maintenance.py
from sqlalchemy import String, DateTime, Enum as SAEnum, ForeignKey, Text, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum
from datetime import datetime
from app.database import Base
from app.core.datetime_utils import now_sp


class TipoManutencao(str, Enum):
    PREVENTIVA = "preventiva"
    CORRETIVA = "corretiva"
    UPGRADE = "upgrade"
    OUTRO = "outro"


class StatusManutencao(str, Enum):
    EM_ANDAMENTO = "em_andamento"
    CONCLUIDA = "concluida"
    CANCELADA = "cancelada"


class DestinoManutencao(str, Enum):
    ARMAZENAMENTO = "armazenamento"
    USUARIO = "usuario"


class Manutencao(Base):
    __tablename__ = "manutencoes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), nullable=False)
    
    # Quem enviou para manutenção
    responsavel_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    # Detalhes da manutenção
    motivo: Mapped[str] = mapped_column(Text, nullable=False)  # Descrição do problema
    tipo: Mapped[TipoManutencao] = mapped_column(SAEnum(TipoManutencao), default=TipoManutencao.CORRETIVA)
    
    # Datas
    data_entrada: Mapped[datetime] = mapped_column(DateTime, default=now_sp)
    data_previsao: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    data_conclusao: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    # Status e resultado
    status: Mapped[StatusManutencao] = mapped_column(SAEnum(StatusManutencao), default=StatusManutencao.EM_ANDAMENTO)
    observacao_conclusao: Mapped[str | None] = mapped_column(Text, nullable=True)
    custo: Mapped[float | None] = mapped_column(Float, nullable=True)
    
    # Destino após manutenção
    destino_tipo: Mapped[DestinoManutencao | None] = mapped_column(SAEnum(DestinoManutencao), nullable=True)
    destino_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    # Relacionamentos
    asset = relationship("Asset", back_populates="manutencoes")
    responsavel = relationship("User", foreign_keys=[responsavel_id], back_populates="manutencoes_responsavel")
    destino_user = relationship("User", foreign_keys=[destino_user_id], back_populates="manutencoes_recebidas")
    solicitacao_origem = relationship("SolicitacaoManutencao", back_populates="manutencao")
