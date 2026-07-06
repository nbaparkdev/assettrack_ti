from sqlalchemy import String, DateTime, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from app.database import Base
from app.core.datetime_utils import now_sp

class EmailLog(Base):
    __tablename__ = "email_logs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    recipient: Mapped[str] = mapped_column(String, index=True, nullable=False)
    subject: Mapped[str] = mapped_column(String, nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_sp)
    status: Mapped[str] = mapped_column(String, nullable=False) # 'SUCCESS' or 'FAILED'
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
