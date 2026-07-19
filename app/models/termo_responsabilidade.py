# app/models/termo_responsabilidade.py
from sqlalchemy import String, ForeignKey, DateTime, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.database import Base
from app.core.datetime_utils import now_sp

class TermoResponsabilidade(Base):
    __tablename__ = "termos_responsabilidade"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    solicitacao_id: Mapped[int | None] = mapped_column(ForeignKey("solicitacoes.id", ondelete="SET NULL"), nullable=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id", ondelete="CASCADE"), nullable=False)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String, default="Pendente") # Pendente, Assinado, Cancelado
    conteudo_termo: Mapped[str] = mapped_column(Text, nullable=False)
    data_criacao: Mapped[datetime] = mapped_column(DateTime, default=now_sp)
    data_assinatura: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relacionamentos
    solicitacao = relationship("Solicitacao")
    asset = relationship("Asset")
    usuario = relationship("User", foreign_keys=[usuario_id])
