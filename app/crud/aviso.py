# app/crud/aviso.py
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from datetime import datetime

from app.crud.base import CRUDBase
from app.models.aviso import Aviso
from app.schemas.aviso import AvisoCreate, AvisoUpdate

class CRUDAviso(CRUDBase[Aviso, AvisoCreate, AvisoUpdate]):
    async def get_active_announcements(self, db: AsyncSession) -> List[Aviso]:
        """
        Retorna todos os avisos ativos e dentro do período programado de exibição.
        """
        from app.core.datetime_utils import now_sp
        now = now_sp()
        query = select(self.model).filter(
            self.model.ativo == True,
            or_(self.model.programado_inicio == None, self.model.programado_inicio <= now),
            or_(self.model.programado_fim == None, self.model.programado_fim >= now)
        ).order_by(self.model.data_cadastro.desc())
        
        result = await db.execute(query)
        return result.scalars().all()

aviso = CRUDAviso(Aviso)
