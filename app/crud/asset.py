
# app/crud/asset.py
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.crud.base import CRUDBase
from app.models.asset import Asset
from app.schemas.asset import AssetCreate, AssetUpdate

class CRUDAsset(CRUDBase[Asset, AssetCreate, AssetUpdate]):
    async def get_by_serial(self, db: AsyncSession, *, serial_number: str) -> Optional[Asset]:
        result = await db.execute(select(Asset).filter(Asset.serial_number == serial_number))
        return result.scalars().first()

    async def get_by_user(self, db: AsyncSession, user_id: int) -> List[Asset]:
        result = await db.execute(select(Asset).filter(Asset.current_user_id == user_id))
        return result.scalars().all()

asset = CRUDAsset(Asset)
