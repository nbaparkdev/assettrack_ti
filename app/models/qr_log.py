# app/models/qr_log.py
"""
Modelo para registro de uso do QR Code.
Mantém auditoria de ações relacionadas a QR Code.
"""
from datetime import datetime
from sqlalchemy import String, DateTime, Integer, Boolean, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from enum import Enum

class QRLogAction(str, Enum):
    """Tipos de ação de QR Code"""
    LOGIN = "login"                     # Login via QR
    LOGIN_FAILED = "login_failed"       # Tentativa de login falhou
    REGENERATE = "regenerate"           # Token regenerado
    PIN_SET = "pin_set"                 # PIN configurado
    PIN_CHANGED = "pin_changed"         # PIN alterado
    PROFILE_VIEW = "profile_view"       # Perfil consultado via QR
    DELIVERY_CONFIRM = "delivery_confirm"  # Entrega confirmada via QR

class QRLog(Base):
    """Log de uso do QR Code para auditoria"""
    __tablename__ = "qr_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Usuário dono do QR (quem teve o QR escaneado/usado)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    # Quem executou a ação (pode ser o próprio usuário ou admin)
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    
    action: Mapped[QRLogAction] = mapped_column(SAEnum(QRLogAction), nullable=False)
    
    # IP de origem da ação
    ip_address: Mapped[str | None] = mapped_column(String, nullable=True)
    
    # Detalhes adicionais (JSON-like string)
    details: Mapped[str | None] = mapped_column(String, nullable=True)
    
    # Se a ação foi bem sucedida
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    
    timestamp: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        nullable=False
    )
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    actor = relationship("User", foreign_keys=[actor_id])
