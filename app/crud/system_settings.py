# app/crud/system_settings.py
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.crud.base import CRUDBase
from app.models.system_settings import SystemSettings

class CRUDSystemSettings(CRUDBase[SystemSettings, BaseModel, BaseModel]):
    async def get_setting(
        self, db: AsyncSession, setting_key: str, default_value: str = ""
    ) -> str:
        result = await db.execute(select(SystemSettings).filter(SystemSettings.setting_key == setting_key))
        obj = result.scalars().first()
        if obj:
            return obj.setting_value
        return default_value

    async def set_setting(
        self, db: AsyncSession, setting_key: str, setting_value: str, descricao: Optional[str] = None
    ) -> SystemSettings:
        result = await db.execute(select(SystemSettings).filter(SystemSettings.setting_key == setting_key))
        obj = result.scalars().first()
        if obj:
            obj.setting_value = setting_value
            if descricao is not None:
                obj.descricao = descricao
            db.add(obj)
            await db.commit()
            await db.refresh(obj)
            return obj
        else:
            obj_in = {
                "setting_key": setting_key,
                "setting_value": setting_value,
                "descricao": descricao
            }
            return await self.create(db, obj_in=obj_in)

system_settings = CRUDSystemSettings(SystemSettings)
