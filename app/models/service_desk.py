# app/models/service_desk.py
from datetime import datetime
from enum import Enum
from typing import Optional, List
from sqlalchemy import String, ForeignKey, DateTime, Text, Float, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class ServiceStatus(str, Enum):
    ABERTO = "Aberto"
    EM_ATENDIMENTO = "Em Atendimento"
    AGUARDANDO_TERCEIRO = "Aguardando Terceiro"
    RESOLVIDO = "Resolvido"
    CANCELADO = "Cancelado"

class ServicePriority(str, Enum):
    BAIXA = "Baixa"
    MEDIA = "Média"
    ALTA = "Alta"
    URGENTE = "Urgente"

class ServiceCategory(Base):
    __tablename__ = "service_categories"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(100), unique=True)
    descricao: Mapped[Optional[str]] = mapped_column(Text)
    setor: Mapped[str] = mapped_column(String(50)) # TI, Infra, RH, etc.
    
    # Relacionamentos
    servicos: Mapped[List["ServiceDefinition"]] = relationship("ServiceDefinition", back_populates="categoria")

class ServiceDefinition(Base):
    __tablename__ = "service_definitions"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    categoria_id: Mapped[int] = mapped_column(ForeignKey("service_categories.id"))
    nome: Mapped[str] = mapped_column(String(100))
    descricao: Mapped[Optional[str]] = mapped_column(Text)
    prioridade_padrao: Mapped[ServicePriority] = mapped_column(String(20), default=ServicePriority.MEDIA)
    tempo_estimado_horas: Mapped[Optional[float]] = mapped_column(Float)
    
    # Relacionamentos
    categoria: Mapped[ServiceCategory] = relationship("ServiceCategory", back_populates="servicos")
    chamados: Mapped[List["ServiceTicket"]] = relationship("ServiceTicket", back_populates="servico")

class ServiceTicket(Base):
    __tablename__ = "service_tickets"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    codigo: Mapped[str] = mapped_column(String(20), unique=True, index=True) # Ex: CH-2026-0001
    servico_id: Mapped[int] = mapped_column(ForeignKey("service_definitions.id"))
    solicitante_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    tecnico_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    
    titulo: Mapped[str] = mapped_column(String(200))
    descricao: Mapped[str] = mapped_column(Text)
    status: Mapped[ServiceStatus] = mapped_column(String(30), default=ServiceStatus.ABERTO)
    prioridade: Mapped[ServicePriority] = mapped_column(String(20))
    
    data_abertura: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    data_atualizacao: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
    data_fechamento: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    solucao: Mapped[Optional[str]] = mapped_column(Text)
    feedback_usuario: Mapped[Optional[str]] = mapped_column(Text)
    avaliacao: Mapped[Optional[int]] = mapped_column(Integer, nullable=True) # 1-5 estrelas
    
    # Relacionamentos
    servico: Mapped[ServiceDefinition] = relationship("ServiceDefinition", back_populates="chamados")
    solicitante: Mapped["User"] = relationship("User", foreign_keys=[solicitante_id])
    tecnico: Mapped[Optional["User"]] = relationship("User", foreign_keys=[tecnico_id])
    interacoes: Mapped[List["ServiceTicketInteraction"]] = relationship("ServiceTicketInteraction", back_populates="ticket", cascade="all, delete-orphan")

class ServiceTicketInteraction(Base):
    __tablename__ = "service_ticket_interactions"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    ticket_id: Mapped[int] = mapped_column(ForeignKey("service_tickets.id"))
    usuario_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    
    mensagem: Mapped[str] = mapped_column(Text)
    data_criacao: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    
    # Tipo de interação: Comentário, Mudança de Status, etc.
    tipo: Mapped[str] = mapped_column(String(50), default="Comentário")
    
    # Relacionamentos
    ticket: Mapped["ServiceTicket"] = relationship("ServiceTicket", back_populates="interacoes")
    usuario: Mapped["User"] = relationship("User")
