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
        """Set or update a system setting.
        Uses explicit SELECT -> UPDATE or sync-sequence -> INSERT to avoid
        PostgreSQL evaluating nextval() PK default during ON CONFLICT logic."""
        # 1. Check if setting key already exists
        check_stmt = text("SELECT id FROM system_settings WHERE setting_key = :key")
        res = await db.execute(check_stmt, {"key": setting_key})
        existing_id = res.scalar()

        if existing_id is not None:
            # Explicit UPDATE by ID — does not touch primary key sequence
            update_stmt = text("""
                UPDATE system_settings
                SET setting_value = :value,
                    descricao = COALESCE(:descricao, descricao)
                WHERE id = :id
            """)
            await db.execute(
                update_stmt,
                {"id": existing_id, "value": setting_value, "descricao": descricao},
            )
        else:
            # Resync sequence before inserting new row to guarantee clean ID
            seq_stmt = text("""
                SELECT setval(
                    pg_get_serial_sequence('system_settings', 'id'),
                    COALESCE((SELECT MAX(id) FROM system_settings), 1)
                )
            """)
            await db.execute(seq_stmt)

            insert_stmt = text("""
                INSERT INTO system_settings (setting_key, setting_value, descricao)
                VALUES (:key, :value, :descricao)
            """)
            await db.execute(
                insert_stmt,
                {"key": setting_key, "value": setting_value, "descricao": descricao},
            )

        if commit:
            await db.commit()


system_settings = CRUDSystemSettings(SystemSettings)
