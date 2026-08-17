from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.datetime_utils import now_sp
from app.database import Base


class Webhook(Base):
    __tablename__ = "webhooks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    url: Mapped[str] = mapped_column(String, nullable=False)
    eventos_permitidos: Mapped[str] = mapped_column(Text, nullable=False) # JSON array of event names stringified
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), default=now_sp, nullable=False)

    logs: Mapped[list["WebhookLog"]] = relationship("WebhookLog", back_populates="webhook", cascade="all, delete-orphan")

class WebhookLog(Base):
    __tablename__ = "webhook_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    webhook_id: Mapped[int] = mapped_column(Integer, ForeignKey("webhooks.id"), nullable=False)
    evento: Mapped[str] = mapped_column(String(100), nullable=False)
    payload_enviado: Mapped[str] = mapped_column(Text, nullable=False) # JSON string
    status_code: Mapped[int] = mapped_column(Integer, nullable=True)
    response_body: Mapped[str] = mapped_column(Text, nullable=True)
    sucesso: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[str] = mapped_column(DateTime(timezone=True), default=now_sp, nullable=False)

    webhook: Mapped["Webhook"] = relationship("Webhook", back_populates="logs")
