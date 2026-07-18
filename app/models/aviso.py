# app/models/aviso.py
from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.database import Base
from app.core.datetime_utils import now_sp

class Aviso(Base):
    __tablename__ = "avisos"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    titulo: Mapped[str] = mapped_column(String, nullable=False)
    texto: Mapped[str | None] = mapped_column(String, nullable=True)
    midia_url: Mapped[str | None] = mapped_column(String, nullable=True)  # URL de imagem ou vídeo
    midia_tipo: Mapped[str | None] = mapped_column(String, nullable=True)  # 'imagem', 'video' ou None
    link_url: Mapped[str | None] = mapped_column(String, nullable=True)   # URL externa ou link interno
    link_texto: Mapped[str | None] = mapped_column(String, nullable=True) # Texto do botão (ex: "Ver Detalhes")
    
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    
    programado_inicio: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    programado_fim: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    data_cadastro: Mapped[datetime] = mapped_column(DateTime, default=now_sp)
