
# app/models/user.py
from sqlalchemy import String, Boolean, Enum as SAEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum
from app.database import Base

class UserRole(str, Enum):
    ADMIN = "admin"
    GERENTE = "gerente_ti"
    TECNICO = "tecnico"
    USUARIO = "usuario_comum"

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    nome: Mapped[str] = mapped_column(String, nullable=False)
    matricula: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=True)
    cargo: Mapped[str] = mapped_column(String, nullable=True)
    role: Mapped[UserRole] = mapped_column(SAEnum(UserRole), default=UserRole.USUARIO)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    avatar_url: Mapped[str | None] = mapped_column(String, nullable=True)
    
    departamento_id: Mapped[int | None] = mapped_column(ForeignKey("departamentos.id"), nullable=True)

    # Relacionamentos
    departamento = relationship("Departamento", back_populates="usuarios", foreign_keys=[departamento_id])
    assets = relationship("Asset", back_populates="current_user")
    solicitacoes = relationship("Solicitacao", foreign_keys="[Solicitacao.solicitante_id]", back_populates="solicitante")
    aprovacoes = relationship("Solicitacao", foreign_keys="[Solicitacao.aprovador_id]", back_populates="aprovador")
    
    # Movimentações onde o usuário é origem ou destino
    movimentacoes_origem = relationship("Movimentacao", foreign_keys="[Movimentacao.de_user_id]", back_populates="de_user")
    movimentacoes_destino = relationship("Movimentacao", foreign_keys="[Movimentacao.para_user_id]", back_populates="para_user")
    
    # Manutenções
    manutencoes_responsavel = relationship("Manutencao", foreign_keys="[Manutencao.responsavel_id]", back_populates="responsavel")
    manutencoes_recebidas = relationship("Manutencao", foreign_keys="[Manutencao.destino_user_id]", back_populates="destino_user")

