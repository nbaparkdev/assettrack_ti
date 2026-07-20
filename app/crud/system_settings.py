# app/crud/system_settings.py
from typing import Optional
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.crud.base import CRUDBase
from app.models.system_settings import SystemSettings


class CRUDSystemSettings(CRUDBase[SystemSettings, BaseModel, BaseModel]):
    async def get_setting(
        self, db: AsyncSession, setting_key: str, default_value: str = ""
    ) -> str:
        result = await db.execute(
            select(SystemSettings).filter(SystemSettings.setting_key == setting_key)
        )
        obj = result.scalars().first()
        return obj.setting_value if obj else default_value

    async def set_setting(
        self,
        db: AsyncSession,
        setting_key: str,
        setting_value: str,
        descricao: Optional[str] = None,
        commit: bool = True,
    ) -> None:
        """Upsert a setting by key. Uses ON CONFLICT DO UPDATE to avoid
        duplicate-key errors when the PK sequence is out of sync."""
        stmt = (
            pg_insert(SystemSettings)
            .values(setting_key=setting_key, setting_value=setting_value, descricao=descricao)
            .on_conflict_do_update(
                index_elements=["setting_key"],
                set_={"setting_value": setting_value, "descricao": descricao},
            )
        )
        await db.execute(stmt)
        if commit:
            await db.commit()


system_settings = CRUDSystemSettings(SystemSettings)
