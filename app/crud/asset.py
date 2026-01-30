
# app/crud/asset.py
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.crud.base import CRUDBase
from app.models.asset import Asset
from app.schemas.asset import AssetCreate, AssetUpdate

class CRUDAsset(CRUDBase[Asset, AssetCreate, AssetUpdate]):
    async def get(self, db: AsyncSession, id: int) -> Optional[Asset]:
        from sqlalchemy.orm import selectinload
        result = await db.execute(
            select(Asset)
            .options(
                selectinload(Asset.current_user),
                selectinload(Asset.current_departamento),
                selectinload(Asset.current_local),
                selectinload(Asset.current_armazenamento)
            )
            .filter(Asset.id == id)
        )
        return result.scalars().first()

    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> List[Asset]:
        from sqlalchemy.orm import selectinload
        result = await db.execute(
            select(Asset)
            .options(
                selectinload(Asset.current_user),
                selectinload(Asset.current_departamento),
                selectinload(Asset.current_local),
                selectinload(Asset.current_armazenamento)
            )
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_serial(self, db: AsyncSession, *, serial_number: str) -> Optional[Asset]:
        from sqlalchemy.orm import selectinload
        result = await db.execute(
            select(Asset)
            .options(
                selectinload(Asset.current_user),
                selectinload(Asset.current_departamento),
                selectinload(Asset.current_local),
                selectinload(Asset.current_armazenamento)
            )
            .filter(Asset.serial_number == serial_number)
        )
        return result.scalars().first()

    async def get_by_user(self, db: AsyncSession, user_id: int) -> List[Asset]:
        from sqlalchemy.orm import selectinload
        result = await db.execute(
            select(Asset)
            .options(
                selectinload(Asset.current_user),
                selectinload(Asset.current_departamento),
                selectinload(Asset.current_local),
                selectinload(Asset.current_armazenamento)
            )
            .filter(Asset.current_user_id == user_id)
        )
        return result.scalars().all()

asset = CRUDAsset(Asset)
