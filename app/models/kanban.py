# app/models/kanban.py
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.datetime_utils import now_sp
from app.database import Base

# Association Table: Project Participants (N:M)
kanban_project_participants = Table(
    "kanban_project_participants",
    Base.metadata,
    Column("project_id", Integer, ForeignKey("kanban_projects.id", ondelete="CASCADE"), primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
)

# Association Table: Card Assignees (N:M)
kanban_card_assignees = Table(
    "kanban_card_assignees",
    Base.metadata,
    Column("card_id", Integer, ForeignKey("kanban_cards.id", ondelete="CASCADE"), primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
)

# Association Table: Card Linked Assets (N:M)
kanban_card_assets = Table(
    "kanban_card_assets",
    Base.metadata,
    Column("card_id", Integer, ForeignKey("kanban_cards.id", ondelete="CASCADE"), primary_key=True),
    Column("asset_id", Integer, ForeignKey("assets.id", ondelete="CASCADE"), primary_key=True)
)

class KanbanProject(Base):
    __tablename__ = "kanban_projects"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    titulo: Mapped[str] = mapped_column(String(255), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text, nullable=True)
    criador_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_sp, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now_sp, onupdate=now_sp, nullable=False)

    # Relationships
    criador: Mapped["User"] = relationship("User", foreign_keys=[criador_id])
    participantes: Mapped[list["User"]] = relationship(
        "User",
        secondary=kanban_project_participants,
        lazy="selectin"
    )
    colunas: Mapped[list["KanbanColumn"]] = relationship(
        "KanbanColumn",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="KanbanColumn.ordem",
        lazy="selectin"
    )
    cards: Mapped[list["KanbanCard"]] = relationship(
        "KanbanCard",
        back_populates="project",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

class KanbanColumn(Base):
    __tablename__ = "kanban_columns"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("kanban_projects.id", ondelete="CASCADE"), nullable=False)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    cor: Mapped[str] = mapped_column(String(30), default="#6B7280", nullable=False) # Badge color
    ordem: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    project: Mapped["KanbanProject"] = relationship("KanbanProject", back_populates="colunas")
    cards: Mapped[list["KanbanCard"]] = relationship(
        "KanbanCard",
        back_populates="column",
        cascade="all, delete-orphan",
        order_by="KanbanCard.ordem",
        lazy="selectin"
    )

class KanbanCard(Base):
    __tablename__ = "kanban_cards"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("kanban_projects.id", ondelete="CASCADE"), nullable=False)
    column_id: Mapped[int] = mapped_column(ForeignKey("kanban_columns.id", ondelete="CASCADE"), nullable=False)
    titulo: Mapped[str] = mapped_column(String(255), nullable=False)
    descricao: Mapped[str | None] = mapped_column(Text, nullable=True) # Markdown text
    criador_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    responsavel_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    prioridade: Mapped[str] = mapped_column(String(20), default="media", nullable=False) # baixa, media, alta, urgente
    data_entrega: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    ordem: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_sp, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now_sp, onupdate=now_sp, nullable=False)

    purchase_request_id: Mapped[int | None] = mapped_column(ForeignKey("purchase_requests.id"), nullable=True)
    material_stock_id: Mapped[int | None] = mapped_column(ForeignKey("material_stocks.id"), nullable=True)
    tipo_item_necessario: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Relationships
    project: Mapped["KanbanProject"] = relationship("KanbanProject", back_populates="cards", lazy="selectin")
    column: Mapped["KanbanColumn"] = relationship("KanbanColumn", back_populates="cards", lazy="selectin")
    criador: Mapped["User"] = relationship("User", foreign_keys=[criador_id], lazy="selectin")
    responsavel: Mapped[Optional["User"]] = relationship("User", foreign_keys=[responsavel_id], lazy="selectin")
    participantes: Mapped[list["User"]] = relationship(
        "User",
        secondary=kanban_card_assignees,
        lazy="selectin"
    )
    ativos: Mapped[list["Asset"]] = relationship(
        "Asset",
        secondary=kanban_card_assets,
        lazy="selectin"
    )
    anexos: Mapped[list["KanbanAttachment"]] = relationship(
        "KanbanAttachment",
        back_populates="card",
        cascade="all, delete-orphan",
        lazy="selectin"
    )
    interacoes: Mapped[list["KanbanCardInteraction"]] = relationship(
        "KanbanCardInteraction",
        back_populates="card",
        cascade="all, delete-orphan",
        order_by="KanbanCardInteraction.created_at.asc()",
        lazy="selectin"
    )
    purchase_request: Mapped[Optional["PurchaseRequest"]] = relationship("PurchaseRequest", lazy="selectin")
    material_stock: Mapped[Optional["MaterialStock"]] = relationship("MaterialStock", lazy="selectin")

class KanbanCardInteraction(Base):
    __tablename__ = "kanban_card_interactions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    card_id: Mapped[int] = mapped_column(ForeignKey("kanban_cards.id", ondelete="CASCADE"), nullable=False, index=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    mensagem: Mapped[str] = mapped_column(Text, nullable=False)
    tipo: Mapped[str] = mapped_column(String(50), default="comentario", nullable=False) # comentario, sistema_movimentacao, sistema_responsavel, sistema_anexo, sistema_suprimentos
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_sp, nullable=False)

    # Relationships
    card: Mapped["KanbanCard"] = relationship("KanbanCard", back_populates="interacoes")
    usuario: Mapped["User"] = relationship("User", lazy="selectin")

class KanbanAttachment(Base):
    __tablename__ = "kanban_attachments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    card_id: Mapped[int] = mapped_column(ForeignKey("kanban_cards.id", ondelete="CASCADE"), nullable=False)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    tipo: Mapped[str] = mapped_column(String(50), nullable=False) # imagem, link, arquivo
    url: Mapped[str] = mapped_column(Text, nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime, default=now_sp, nullable=False)

    # Relationship
    card: Mapped["KanbanCard"] = relationship("KanbanCard", back_populates="anexos")


class KanbanNotification(Base):
    __tablename__ = "kanban_notifications"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("kanban_projects.id", ondelete="CASCADE"), nullable=True)
    card_id: Mapped[int | None] = mapped_column(ForeignKey("kanban_cards.id", ondelete="CASCADE"), nullable=True)
    autor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    tipo: Mapped[str] = mapped_column(String(50), nullable=False) # PROJETO_ADICIONADO, CARTAO_ATRIBUIDO, CARTAO_MOVIMENTADO, ANEXO_ADICIONADO
    titulo: Mapped[str] = mapped_column(String(255), nullable=False)
    mensagem: Mapped[str] = mapped_column(Text, nullable=False)
    link: Mapped[str | None] = mapped_column(String(255), nullable=True)
    lida: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_sp, nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    autor: Mapped[Optional["User"]] = relationship("User", foreign_keys=[autor_id])
    project: Mapped[Optional["KanbanProject"]] = relationship("KanbanProject")
    card: Mapped[Optional["KanbanCard"]] = relationship("KanbanCard")
