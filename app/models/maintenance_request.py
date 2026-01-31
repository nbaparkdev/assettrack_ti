
# app/models/maintenance_request.py
from sqlalchemy import String, DateTime, Enum as SAEnum, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum
from datetime import datetime
from app.database import Base


class PrioridadeSolicitacao(str, Enum):
    BAIXA = "baixa"
    MEDIA = "media"
    ALTA = "alta"
    CRITICA = "critica"


class StatusSolicitacaoManutencao(str, Enum):
    PENDENTE = "pendente"
    ACEITA = "aceita"
    EM_ANDAMENTO = "em_andamento"
    AGUARDANDO_ENTREGA = "aguardando_entrega"  # Técnico concluiu, aguardando entrega ao usuário
    ENTREGUE = "entregue"  # Técnico entregou, aguardando confirmação final do usuário
    CONCLUIDA = "concluida"  # Usuário confirmou recebimento
    REJEITADA = "rejeitada"


class SolicitacaoManutencao(Base):
    __tablename__ = "solicitacoes_manutencao"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Quem solicitou
    solicitante_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    # Ativo com problema
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), nullable=False)
    
    # Detalhes do problema
    descricao: Mapped[str] = mapped_column(Text, nullable=False)
    prioridade: Mapped[PrioridadeSolicitacao] = mapped_column(
        SAEnum(PrioridadeSolicitacao), 
        default=PrioridadeSolicitacao.MEDIA
    )
    
    # Datas
    data_solicitacao: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    data_resposta: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    data_conclusao_tecnico: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)  # Quando técnico concluiu
    data_entrega: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)  # Quando usuário confirmou recebimento
    
    # Status e resposta
    status: Mapped[StatusSolicitacaoManutencao] = mapped_column(
        SAEnum(StatusSolicitacaoManutencao), 
        default=StatusSolicitacaoManutencao.PENDENTE
    )
    
    # Técnico responsável (quem aceitou)
    responsavel_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    observacao_resposta: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Link para manutenção criada (quando aceita)
    manutencao_id: Mapped[int | None] = mapped_column(ForeignKey("manutencoes.id"), nullable=True)

    # Relacionamentos
    solicitante = relationship("User", foreign_keys=[solicitante_id], back_populates="solicitacoes_manutencao")
    responsavel = relationship("User", foreign_keys=[responsavel_id], back_populates="solicitacoes_manutencao_responsavel")
    asset = relationship("Asset", back_populates="solicitacoes_manutencao")
    manutencao = relationship("Manutencao", back_populates="solicitacao_origem")
