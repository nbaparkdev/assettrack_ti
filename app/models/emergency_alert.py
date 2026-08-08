# app/models/emergency_alert.py
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime
from app.database import Base
from app.core.datetime_utils import now_sp

class EmergencyAlert(Base):
    __tablename__ = "emergency_alerts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    usuario_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    usuario_nome: Mapped[str] = mapped_column(String, nullable=False)
    setor_nome: Mapped[str | None] = mapped_column(String, nullable=True)
    ativo_nome: Mapped[str | None] = mapped_column(String, nullable=True)
    motivo: Mapped[str] = mapped_column(Text, nullable=False)
    atendido: Mapped[bool] = mapped_column(Boolean, default=False)
    atendido_por_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_sp)

    # Relationships
    usuario = relationship("User", foreign_keys=[usuario_id])
    atendido_por = relationship("User", foreign_keys=[atendido_por_id])
