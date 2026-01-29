
# app/models/location.py
from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Departamento(Base):
    __tablename__ = "departamentos"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    responsavel_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    # Relacionamentos
    usuarios = relationship("User", back_populates="departamento", foreign_keys="[User.departamento_id]")
    locais = relationship("Localizacao", back_populates="departamento")
    assets = relationship("Asset", back_populates="current_departamento")

class Localizacao(Base):
    __tablename__ = "locais"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String, nullable=False) # Ex: Sala 101, Andar 3
    departamento_id: Mapped[int | None] = mapped_column(ForeignKey("departamentos.id"), nullable=True)

    # Relacionamentos
    departamento = relationship("Departamento", back_populates="locais")
    assets = relationship("Asset", back_populates="current_local")

class Armazenamento(Base):
    __tablename__ = "armazenamentos"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String, unique=True, nullable=False) # Ex: Depósito Central
    capacidade_max: Mapped[int] = mapped_column(Integer, default=0)
    tipo_itens: Mapped[str | None] = mapped_column(String, nullable=True)

    # Relacionamentos
    assets = relationship("Asset", back_populates="current_armazenamento")
