# app/models/system_settings.py
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class SystemSettings(Base):
    __tablename__ = "system_settings"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    setting_key: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    setting_value: Mapped[str] = mapped_column(String, nullable=False)
    descricao: Mapped[str | None] = mapped_column(String, nullable=True)
