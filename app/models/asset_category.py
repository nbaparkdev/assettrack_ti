from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List, TYPE_CHECKING
from app.database import Base

if TYPE_CHECKING:
    from app.models.asset import Asset


class AssetCategory(Base):
    __tablename__ = "asset_categories"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    descricao: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    assets: Mapped[List["Asset"]] = relationship("Asset", back_populates="categoria")
