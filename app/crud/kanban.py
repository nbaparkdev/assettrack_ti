# app/crud/kanban.py
from datetime import datetime

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.asset import Asset
from app.models.kanban import (
    KanbanAttachment,
    KanbanCard,
    KanbanCardInteraction,
    KanbanColumn,
    KanbanProject,
)
from app.models.user import User

DEFAULT_COLUMNS = [
    {"nome": "A Fazer", "cor": "#3B82F6", "ordem": 0},          # Blue
    {"nome": "Em Andamento", "cor": "#F59E0B", "ordem": 1},     # Amber
    {"nome": "Aguardando Compras", "cor": "#8B5CF6", "ordem": 2}, # Purple/Indigo
    {"nome": "Concluído", "cor": "#10B981", "ordem": 3}        # Emerald
]

class CRUDKanban:
    async def get_user_projects(
        self,
        db: AsyncSession,
        user: User,
        include_archived: bool = False
    ) -> list[KanbanProject]:
        stmt = select(KanbanProject).options(
            selectinload(KanbanProject.criador),
            selectinload(KanbanProject.participantes),
            selectinload(KanbanProject.colunas),
            selectinload(KanbanProject.cards)
        )

        role_str = user.role.value.lower() if hasattr(user.role, 'value') else str(user.role).lower()
        
        # User role filtering
        if role_str == "usuario_comum":
            # Must be creator or participant
            stmt = stmt.where(
                or_(
                    KanbanProject.criador_id == user.id,
                    KanbanProject.participantes.any(User.id == user.id)
                )
            )

        if not include_archived:
            stmt = stmt.where(KanbanProject.is_archived == False)

        stmt = stmt.where(KanbanProject.is_active == True)
        stmt = stmt.order_by(KanbanProject.updated_at.desc())

        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def count_user_active_projects(self, db: AsyncSession, user: User) -> int:
        role_str = user.role.value.lower() if hasattr(user.role, 'value') else str(user.role).lower()
        if role_str != "usuario_comum":
            return 1 # Has access to global module anyway

        stmt = select(func.count(KanbanProject.id)).where(
            KanbanProject.is_active == True,
            KanbanProject.is_archived == False,
            or_(
                KanbanProject.criador_id == user.id,
                KanbanProject.participantes.any(User.id == user.id)
            )
        )
        res = await db.execute(stmt)
        return res.scalar() or 0

    async def get_project_by_id(
        self,
        db: AsyncSession,
        project_id: int
    ) -> KanbanProject | None:
        stmt = select(KanbanProject).options(
            selectinload(KanbanProject.criador),
            selectinload(KanbanProject.participantes),
            selectinload(KanbanProject.colunas).selectinload(KanbanColumn.cards).selectinload(KanbanCard.criador),
            selectinload(KanbanProject.colunas).selectinload(KanbanColumn.cards).selectinload(KanbanCard.responsavel),
            selectinload(KanbanProject.colunas).selectinload(KanbanColumn.cards).selectinload(KanbanCard.participantes),
            selectinload(KanbanProject.colunas).selectinload(KanbanColumn.cards).selectinload(KanbanCard.ativos),
            selectinload(KanbanProject.colunas).selectinload(KanbanColumn.cards).selectinload(KanbanCard.anexos),
            selectinload(KanbanProject.colunas).selectinload(KanbanColumn.cards).selectinload(KanbanCard.interacoes).selectinload(KanbanCardInteraction.usuario),
            selectinload(KanbanProject.colunas).selectinload(KanbanColumn.cards).selectinload(KanbanCard.purchase_request),
            selectinload(KanbanProject.colunas).selectinload(KanbanColumn.cards).selectinload(KanbanCard.material_stock)
        ).where(KanbanProject.id == project_id).execution_options(populate_existing=True)

        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_card_by_id(
        self,
        db: AsyncSession,
        card_id: int
    ) -> KanbanCard | None:
        stmt = select(KanbanCard).options(
            selectinload(KanbanCard.criador),
            selectinload(KanbanCard.responsavel),
            selectinload(KanbanCard.participantes),
            selectinload(KanbanCard.ativos),
            selectinload(KanbanCard.anexos),
            selectinload(KanbanCard.interacoes).selectinload(KanbanCardInteraction.usuario),
            selectinload(KanbanCard.purchase_request),
            selectinload(KanbanCard.material_stock)
        ).where(KanbanCard.id == card_id).execution_options(populate_existing=True)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    async def create_project(
        self,
        db: AsyncSession,
        titulo: str,
        descricao: str | None,
        criador_id: int,
        participant_ids: list[int],
        columns_data: list[dict] | None = None
    ) -> KanbanProject:
        all_participant_ids = list(set(participant_ids + [criador_id]))
        users_list = []
        if all_participant_ids:
            users_stmt = select(User).where(User.id.in_(all_participant_ids))
            res = await db.execute(users_stmt)
            users_list = list(res.scalars().all())

        project = KanbanProject(
            titulo=titulo.strip(),
            descricao=descricao.strip() if descricao else None,
            criador_id=criador_id,
            participantes=users_list
        )
        db.add(project)
        await db.flush()

        # Initialize columns
        cols_to_create = columns_data if columns_data else DEFAULT_COLUMNS
        for idx, col in enumerate(cols_to_create):
            new_col = KanbanColumn(
                project_id=project.id,
                nome=col["nome"],
                cor=col.get("cor", "#6B7280"),
                ordem=idx,
                is_default=True
            )
            db.add(new_col)

        await db.commit()
        return await self.get_project_by_id(db, project.id)

    async def update_project(
        self,
        db: AsyncSession,
        project: KanbanProject,
        titulo: str,
        descricao: str | None,
        participant_ids: list[int],
        is_active: bool,
        is_archived: bool
    ) -> KanbanProject:
        project.titulo = titulo.strip()
        project.descricao = descricao.strip() if descricao else None
        project.is_active = is_active
        project.is_archived = is_archived

        # Always ensure creator is in participants
        all_participant_ids = list(set(participant_ids + [project.criador_id]))
        users_stmt = select(User).where(User.id.in_(all_participant_ids))
        res = await db.execute(users_stmt)
        project.participantes = list(res.scalars().all())

        await db.commit()
        return await self.get_project_by_id(db, project.id)

    async def add_column(
        self,
        db: AsyncSession,
        project_id: int,
        nome: str,
        cor: str = "#6B7280"
    ) -> KanbanColumn:
        res = await db.execute(
            select(func.max(KanbanColumn.ordem)).where(KanbanColumn.project_id == project_id)
        )
        max_ordem = res.scalar() or 0
        new_col = KanbanColumn(
            project_id=project_id,
            nome=nome.strip(),
            cor=cor,
            ordem=max_ordem + 1,
            is_default=False
        )
        db.add(new_col)
        await db.commit()
        await db.refresh(new_col)
        return new_col

    async def create_card(
        self,
        db: AsyncSession,
        project_id: int,
        column_id: int,
        titulo: str,
        descricao: str | None,
        criador_id: int,
        responsavel_id: int | None,
        assignee_ids: list[int],
        asset_ids: list[int],
        prioridade: str = "media",
        data_entrega: datetime | None = None
    ) -> KanbanCard:
        # Calculate max order in current column
        res = await db.execute(
            select(func.max(KanbanCard.ordem)).where(KanbanCard.column_id == column_id)
        )
        max_ordem = res.scalar()
        next_ordem = (max_ordem + 1) if max_ordem is not None else 0

        assignees_list = []
        if assignee_ids:
            u_stmt = select(User).where(User.id.in_(assignee_ids))
            u_res = await db.execute(u_stmt)
            assignees_list = list(u_res.scalars().all())

        assets_list = []
        if asset_ids:
            a_stmt = select(Asset).where(Asset.id.in_(asset_ids))
            a_res = await db.execute(a_stmt)
            assets_list = list(a_res.scalars().all())

        card = KanbanCard(
            project_id=project_id,
            column_id=column_id,
            titulo=titulo.strip(),
            descricao=descricao.strip() if descricao else None,
            criador_id=criador_id,
            responsavel_id=responsavel_id,
            prioridade=prioridade,
            data_entrega=data_entrega,
            ordem=next_ordem,
            participantes=assignees_list,
            ativos=assets_list
        )
        db.add(card)
        await db.commit()
        
        card_stmt = select(KanbanCard).options(
            selectinload(KanbanCard.criador),
            selectinload(KanbanCard.responsavel),
            selectinload(KanbanCard.participantes),
            selectinload(KanbanCard.ativos),
            selectinload(KanbanCard.anexos),
            selectinload(KanbanCard.purchase_request),
            selectinload(KanbanCard.material_stock)
        ).where(KanbanCard.id == card.id)
        res_card = await db.execute(card_stmt)
        return res_card.scalar_one()

    async def update_card(
        self,
        db: AsyncSession,
        card: KanbanCard,
        titulo: str,
        descricao: str | None,
        column_id: int,
        responsavel_id: int | None,
        assignee_ids: list[int],
        asset_ids: list[int],
        prioridade: str,
        data_entrega: datetime | None = None
    ) -> KanbanCard:
        card.titulo = titulo.strip()
        card.descricao = descricao.strip() if descricao else None
        card.column_id = column_id
        card.responsavel_id = responsavel_id
        card.prioridade = prioridade
        card.data_entrega = data_entrega

        if assignee_ids:
            u_stmt = select(User).where(User.id.in_(assignee_ids))
            card.participantes = list((await db.execute(u_stmt)).scalars().all())
        else:
            card.participantes = []

        if asset_ids:
            a_stmt = select(Asset).where(Asset.id.in_(asset_ids))
            card.ativos = list((await db.execute(a_stmt)).scalars().all())
        else:
            card.ativos = []

        await db.commit()
        await db.refresh(card)
        return card

    async def move_card(
        self,
        db: AsyncSession,
        card_id: int,
        target_column_id: int,
        target_order: int
    ) -> KanbanCard | None:
        card = await db.get(KanbanCard, card_id)
        if not card:
            return None

        card.column_id = target_column_id
        card.ordem = target_order
        await db.commit()
        await db.refresh(card)
        return card

    async def delete_card(self, db: AsyncSession, card: KanbanCard) -> None:
        await db.delete(card)
        await db.commit()

    async def add_attachment(
        self,
        db: AsyncSession,
        card_id: int,
        nome: str,
        tipo: str,
        url: str
    ) -> KanbanAttachment:
        attachment = KanbanAttachment(
            card_id=card_id,
            nome=nome,
            tipo=tipo,
            url=url
        )
        db.add(attachment)
        await db.commit()
        await db.refresh(attachment)
        return attachment

    async def remove_attachment(self, db: AsyncSession, attachment_id: int) -> None:
        attachment = await db.get(KanbanAttachment, attachment_id)
        if attachment:
            await db.delete(attachment)
            await db.commit()

    async def add_interaction(
        self,
        db: AsyncSession,
        card_id: int,
        usuario_id: int,
        mensagem: str,
        tipo: str = "comentario"
    ) -> KanbanCardInteraction:
        interaction = KanbanCardInteraction(
            card_id=card_id,
            usuario_id=usuario_id,
            mensagem=mensagem.strip(),
            tipo=tipo
        )
        db.add(interaction)
        await db.commit()
        await db.refresh(interaction)
        return interaction


crud_kanban = CRUDKanban()
