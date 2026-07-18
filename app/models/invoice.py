# app/models/invoice.py
from sqlalchemy import String, ForeignKey, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.database import Base
from app.core.datetime_utils import now_sp

class NotaFiscal(Base):
    __tablename__ = "notas_fiscais"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    numero_nota: Mapped[str] = mapped_column(String, index=True, nullable=False)
    fornecedor_id: Mapped[int] = mapped_column(ForeignKey("fornecedores.id"), nullable=False)
    xml_path: Mapped[str | None] = mapped_column(String, nullable=True)
    data_cadastro: Mapped[datetime] = mapped_column(DateTime, default=now_sp)
    
    # Extraídos do XML
    data_emissao: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    valor_total: Mapped[float | None] = mapped_column(nullable=True)
    natureza_operacao: Mapped[str | None] = mapped_column(String, nullable=True)
    emitente_nome: Mapped[str | None] = mapped_column(String, nullable=True)
    emitente_cnpj: Mapped[str | None] = mapped_column(String, nullable=True)
    destinatario_nome: Mapped[str | None] = mapped_column(String, nullable=True)
    destinatario_cnpj: Mapped[str | None] = mapped_column(String, nullable=True)
    itens: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # Relacionamentos
    fornecedor = relationship("Fornecedor", back_populates="notas_fiscais")
    assets = relationship("Asset", back_populates="nota_fiscal")
