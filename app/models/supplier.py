# app/models/supplier.py
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Fornecedor(Base):
    __tablename__ = "fornecedores"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String, index=True, nullable=False)
    razao_social: Mapped[str | None] = mapped_column(String, nullable=True)
    cnpj: Mapped[str | None] = mapped_column(String, unique=True, index=True, nullable=True)
    email: Mapped[str | None] = mapped_column(String, nullable=True)
    telefone: Mapped[str | None] = mapped_column(String, nullable=True)
    endereco: Mapped[str | None] = mapped_column(String, nullable=True)
    cidade: Mapped[str | None] = mapped_column(String, nullable=True)
    estado: Mapped[str | None] = mapped_column(String, nullable=True)
    tipo_fornecedor: Mapped[str | None] = mapped_column(String, nullable=True)

    # Relacionamentos
    notas_fiscais = relationship("NotaFiscal", back_populates="fornecedor", cascade="all, delete-orphan")
    assets = relationship("Asset", back_populates="fornecedor")
