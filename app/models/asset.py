
# app/models/asset.py
from sqlalchemy import String, Float, DateTime, Enum as SAEnum, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from enum import Enum
from datetime import datetime
from app.database import Base

class AssetStatus(str, Enum):
    DISPONIVEL = "Disponível"
    EM_USO = "Em uso"
    MANUTENCAO = "Manutenção"
    ARMAZENADO = "Armazenado"
    BAIXADO = "Baixado"

class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String, index=True, nullable=False)
    serial_number: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    modelo: Mapped[str] = mapped_column(String, nullable=True)
    descricao: Mapped[str | None] = mapped_column(String, nullable=True)
    data_aquisicao: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    valor: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    status: Mapped[AssetStatus] = mapped_column(SAEnum(AssetStatus), default=AssetStatus.DISPONIVEL, index=True)
    
    qr_code_path: Mapped[str | None] = mapped_column(String, nullable=True)
    foto_path: Mapped[str | None] = mapped_column(String, nullable=True)

    # Localização Atual / Responsabilidade
    current_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    current_departamento_id: Mapped[int | None] = mapped_column(ForeignKey("departamentos.id"), nullable=True)
    current_local_id: Mapped[int | None] = mapped_column(ForeignKey("locais.id"), nullable=True)
    current_armazenamento_id: Mapped[int | None] = mapped_column(ForeignKey("armazenamentos.id"), nullable=True)

    # Relacionamentos
    current_user = relationship("User", back_populates="assets")
    current_departamento = relationship("Departamento", back_populates="assets")
    current_local = relationship("Localizacao", back_populates="assets")
    current_armazenamento = relationship("Armazenamento", back_populates="assets")
    
    movimentacoes = relationship("Movimentacao", back_populates="asset", cascade="all, delete-orphan")
    solicitacoes = relationship("Solicitacao", back_populates="asset", cascade="all, delete-orphan")
    manutencoes = relationship("Manutencao", back_populates="asset", cascade="all, delete-orphan")
    solicitacoes_manutencao = relationship("SolicitacaoManutencao", back_populates="asset", cascade="all, delete-orphan")

