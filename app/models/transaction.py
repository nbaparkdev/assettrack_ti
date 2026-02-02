
# app/models/transaction.py
from sqlalchemy import String, DateTime, Enum as SAEnum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum
from datetime import datetime
from app.database import Base
from app.core.datetime_utils import now_sp

class TipoMovimentacao(str, Enum):
    EMPRESTIMO = "empréstimo"
    DEVOLUCAO = "devolução"
    TRANSFERENCIA = "transferência"
    MANUTENCAO = "manutenção"
    BAIXA = "baixa"
    CADASTRO = "cadastro"

class StatusSolicitacao(str, Enum):
    PENDENTE = "Pendente"
    APROVADA = "Aprovada"
    ENTREGUE = "Entregue"  # Novo - confirmação de recebimento
    REJEITADA = "Rejeitada"
    CANCELADA = "Cancelada"

class Movimentacao(Base):
    __tablename__ = "movimentacoes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), nullable=False)
    data: Mapped[datetime] = mapped_column(DateTime, default=now_sp)
    tipo: Mapped[TipoMovimentacao] = mapped_column(SAEnum(TipoMovimentacao), nullable=False)
    
    # Origem e Destino (Users)
    de_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    para_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    
    # Origem e Destino (Departamentos - opcional, dependendo da lógica)
    de_departamento_id: Mapped[int | None] = mapped_column(ForeignKey("departamentos.id"), nullable=True)
    para_departamento_id: Mapped[int | None] = mapped_column(ForeignKey("departamentos.id"), nullable=True)
    
    observacao: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relacionamentos
    asset = relationship("Asset", back_populates="movimentacoes")
    de_user = relationship("User", foreign_keys=[de_user_id], back_populates="movimentacoes_origem")
    para_user = relationship("User", foreign_keys=[para_user_id], back_populates="movimentacoes_destino")


class Solicitacao(Base):
    __tablename__ = "solicitacoes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    solicitante_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    asset_id: Mapped[int | None] = mapped_column(ForeignKey("assets.id"), nullable=True) # Pode solicitar um tipo, não necessariamente um asset específico, mas por enquanto linkamos direto se souber
    
    data_solicitacao: Mapped[datetime] = mapped_column(DateTime, default=now_sp)
    motivo: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[StatusSolicitacao] = mapped_column(SAEnum(StatusSolicitacao), default=StatusSolicitacao.PENDENTE)
    
    # Aprovação
    aprovador_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    data_aprovacao: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    data_prevista_devolucao: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    # Confirmação de Entrega (via QR Code ou manual)
    data_entrega: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    confirmado_por_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)  # Admin/Gerente que confirmou
    confirmado_via_qr: Mapped[bool | None] = mapped_column(default=False)  # Se foi via QR do usuário
    observacao_entrega: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relacionamentos
    solicitante = relationship("User", foreign_keys=[solicitante_id], back_populates="solicitacoes")
    aprovador = relationship("User", foreign_keys=[aprovador_id], back_populates="aprovacoes")
    confirmador = relationship("User", foreign_keys=[confirmado_por_id])
    asset = relationship("Asset", back_populates="solicitacoes")
