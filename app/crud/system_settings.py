# app/crud/system_settings.py
from typing import Optional
from sqlalchemy import select, text
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
        """Upsert a setting by key using raw SQL to avoid SQLAlchemy adding
        RETURNING id, which would trigger the PK sequence and cause duplicate
        key errors when the sequence is out of sync with existing data."""
        stmt = text("""
            INSERT INTO system_settings (setting_key, setting_value, descricao)
            VALUES (:key, :value, :descricao)
            ON CONFLICT (setting_key) DO UPDATE
                SET setting_value = EXCLUDED.setting_value,
                    descricao    = COALESCE(EXCLUDED.descricao, system_settings.descricao)
        """)
        await db.execute(stmt, {"key": setting_key, "value": setting_value, "descricao": descricao})
        if commit:
            await db.commit()


system_settings = CRUDSystemSettings(SystemSettings)
