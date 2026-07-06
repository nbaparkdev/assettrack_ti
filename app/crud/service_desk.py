# app/crud/service_desk.py
from typing import List, Optional
from datetime import datetime
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.datetime_utils import now_sp
from app.crud.base import CRUDBase
from app.models.service_desk import ServiceCategory, ServiceDefinition, ServiceTicket, ServiceStatus
from app.models.user import User
from app.schemas.service_desk import (
    ServiceCategoryCreate, ServiceCategoryUpdate,
    ServiceDefinitionCreate, ServiceDefinitionUpdate,
    ServiceTicketCreate, ServiceTicketUpdate,
    ServiceTicketInteractionCreate
)
from app.models.service_desk import ServiceCategory, ServiceDefinition, ServiceTicket, ServiceStatus, ServiceTicketInteraction

class CRUDServiceCategory(CRUDBase[ServiceCategory, ServiceCategoryCreate, ServiceCategoryUpdate]):
    async def get_all_with_definitions(self, db: AsyncSession) -> List[ServiceCategory]:
        result = await db.execute(
            select(ServiceCategory).options(selectinload(ServiceCategory.servicos))
        )
        return result.scalars().all()

class CRUDServiceDefinition(CRUDBase[ServiceDefinition, ServiceDefinitionCreate, ServiceDefinitionUpdate]):
    async def get_by_category(self, db: AsyncSession, category_id: int) -> List[ServiceDefinition]:
        result = await db.execute(
            select(ServiceDefinition).filter(ServiceDefinition.categoria_id == category_id)
        )
        return result.scalars().all()

class CRUDServiceTicket(CRUDBase[ServiceTicket, ServiceTicketCreate, ServiceTicketUpdate]):
    async def generate_codigo(self, db: AsyncSession) -> str:
        year = now_sp().year
        count_query = select(func.count()).select_from(ServiceTicket).filter(
            ServiceTicket.data_abertura >= datetime(year, 1, 1)
        )
        count = await db.scalar(count_query) or 0
        return f"CH-{year}-{(count + 1):04d}"

    async def create_with_codigo(
        self, db: AsyncSession, *, obj_in: ServiceTicketCreate, solicitante_id: int
    ) -> ServiceTicket:
        codigo = await self.generate_codigo(db)
        obj_data = obj_in.model_dump()
        db_obj = ServiceTicket(
            **obj_data,
            codigo=codigo,
            solicitante_id=solicitante_id,
            data_abertura=now_sp()
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_full(self, db: AsyncSession, ticket_id: str) -> Optional[ServiceTicket]:
        stmt = select(ServiceTicket).options(
            selectinload(ServiceTicket.servico).selectinload(ServiceDefinition.categoria),
            selectinload(ServiceTicket.solicitante),
            selectinload(ServiceTicket.tecnico),
            selectinload(ServiceTicket.interacoes).selectinload(ServiceTicketInteraction.usuario)
        )
        if str(ticket_id).isdigit():
            stmt = stmt.filter(ServiceTicket.id == int(ticket_id))
        else:
            stmt = stmt.filter(ServiceTicket.codigo == ticket_id)
            
        result = await db.execute(stmt)
        return result.scalars().first()

    async def get_user_tickets(self, db: AsyncSession, user_id: int) -> List[ServiceTicket]:
        result = await db.execute(
            select(ServiceTicket)
            .options(selectinload(ServiceTicket.servico))
            .filter(ServiceTicket.solicitante_id == user_id)
            .order_by(ServiceTicket.data_abertura.desc())
        )
        return result.scalars().all()

    async def search_tickets(
        self, 
        db: AsyncSession, 
        *, 
        query: Optional[str] = None,
        status: Optional[ServiceStatus] = None,
        prioridade: Optional[str] = None,
        categoria_id: Optional[int] = None,
        solicitante_id: Optional[int] = None,
        data_inicio: Optional[datetime] = None,
        data_fim: Optional[datetime] = None
    ) -> List[ServiceTicket]:
        stmt = select(ServiceTicket).options(
            selectinload(ServiceTicket.servico).selectinload(ServiceDefinition.categoria),
            selectinload(ServiceTicket.solicitante).selectinload(User.departamento)
        )
        
        if query:
            stmt = stmt.where(or_(
                ServiceTicket.codigo.ilike(f"%{query}%"),
                ServiceTicket.titulo.ilike(f"%{query}%"),
                ServiceTicket.descricao.ilike(f"%{query}%")
            ))
            
        if status:
            stmt = stmt.where(ServiceTicket.status == status)
            
        if prioridade:
            stmt = stmt.where(ServiceTicket.prioridade == prioridade)
            
        if categoria_id:
            stmt = stmt.join(ServiceDefinition).where(ServiceDefinition.categoria_id == categoria_id)
            
        if solicitante_id:
            stmt = stmt.where(ServiceTicket.solicitante_id == solicitante_id)
            
        if data_inicio:
            stmt = stmt.where(ServiceTicket.data_abertura >= data_inicio)
            
        if data_fim:
            stmt = stmt.where(ServiceTicket.data_abertura <= data_fim)
            
        stmt = stmt.order_by(ServiceTicket.data_abertura.desc())
        result = await db.execute(stmt)
        return result.scalars().all()

class CRUDServiceTicketInteraction(CRUDBase[ServiceTicketInteraction, ServiceTicketInteractionCreate, None]):
    async def create_with_user(
        self, db: AsyncSession, *, obj_in: ServiceTicketInteractionCreate, usuario_id: int
    ) -> ServiceTicketInteraction:
        db_obj = ServiceTicketInteraction(
            **obj_in.model_dump(),
            usuario_id=usuario_id,
            data_criacao=now_sp()
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

category = CRUDServiceCategory(ServiceCategory)
definition = CRUDServiceDefinition(ServiceDefinition)
ticket = CRUDServiceTicket(ServiceTicket)
interaction = CRUDServiceTicketInteraction(ServiceTicketInteraction)
