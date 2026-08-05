# app/services/kanban_notification_service.py
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.kanban import KanbanNotification, KanbanProject, KanbanCard
from app.models.user import User

async def create_kanban_notification(
    db: AsyncSession,
    user_id: int,
    tipo: str,
    titulo: str,
    mensagem: str,
    project_id: Optional[int] = None,
    card_id: Optional[int] = None,
    autor_id: Optional[int] = None,
    link: Optional[str] = None
) -> KanbanNotification:
    """Helper to create and persist a Kanban notification for a target user."""
    notif = KanbanNotification(
        user_id=user_id,
        project_id=project_id,
        card_id=card_id,
        autor_id=autor_id,
        tipo=tipo,
        titulo=titulo,
        mensagem=mensagem,
        link=link or (f"/kanban/projetos/{project_id}" if project_id else "/kanban"),
        lida=False
    )
    db.add(notif)
    return notif

async def notify_users_added_to_project(
    db: AsyncSession,
    project: KanbanProject,
    user_ids: List[int],
    author: User
):
    """Notify users that they have been added to a Kanban project."""
    autor_nome = author.nome if author else "Um administrador"
    proj_title = project.titulo if project else "Projeto"
    proj_id = project.id if project else None

    for uid in set(user_ids):
        if author and uid == author.id:
            continue # Don't notify the author
        await create_kanban_notification(
            db=db,
            user_id=uid,
            project_id=proj_id,
            autor_id=author.id if author else None,
            tipo="PROJETO_ADICIONADO",
            titulo=f"Novo Projeto: {proj_title}",
            mensagem=f"{autor_nome} adicionou você ao projeto '{proj_title}'.",
            link=f"/kanban/projetos/{proj_id}" if proj_id else "/kanban"
        )
    await db.commit()

async def notify_card_assigned(
    db: AsyncSession,
    card: KanbanCard,
    user_ids: List[int],
    author: User
):
    """Notify users assigned to a specific card."""
    autor_nome = author.nome if author else "Um usuário"
    
    proj_title = "Projeto"
    if card and card.project_id:
        proj = await db.get(KanbanProject, card.project_id)
        if proj:
            proj_title = proj.titulo

    for uid in set(user_ids):
        if author and uid == author.id:
            continue
        await create_kanban_notification(
            db=db,
            user_id=uid,
            project_id=card.project_id,
            card_id=card.id,
            autor_id=author.id if author else None,
            tipo="CARTAO_ATRIBUIDO",
            titulo=f"Atribuído ao Cartão: {card.titulo}",
            mensagem=f"{autor_nome} atribuiu você ao cartão '{card.titulo}' no projeto '{proj_title}'.",
            link=f"/kanban/projetos/{card.project_id}?card={card.id}"
        )
    await db.commit()

async def notify_card_moved(
    db: AsyncSession,
    card: KanbanCard,
    source_col_name: str,
    target_col_name: str,
    author: User
):
    """Notify project participants and card assignees when a card moves columns."""
    if source_col_name == target_col_name:
        return
    
    autor_nome = author.nome if author else "Um participante"
    
    proj_title = "Projeto"
    project = None
    if card and card.project_id:
        stmt = select(KanbanProject).options(selectinload(KanbanProject.participantes)).where(KanbanProject.id == card.project_id)
        res = await db.execute(stmt)
        project = res.scalars().first()
        if project:
            proj_title = project.titulo
    
    # Target users: project participants + card participants + card responsavel
    recipients = set()
    if project and project.participantes:
        for p in project.participantes:
            recipients.add(p.id)
    if project and project.criador_id:
        recipients.add(project.criador_id)
    if card.participantes:
        for p in card.participantes:
            recipients.add(p.id)
    if card.responsavel_id:
        recipients.add(card.responsavel_id)
    
    # Remove author
    if author and author.id in recipients:
        recipients.remove(author.id)

    for uid in recipients:
        await create_kanban_notification(
            db=db,
            user_id=uid,
            project_id=card.project_id,
            card_id=card.id,
            autor_id=author.id if author else None,
            tipo="CARTAO_MOVIMENTADO",
            titulo=f"Progresso: {card.titulo}",
            mensagem=f"{autor_nome} moveu o cartão '{card.titulo}' para '{target_col_name}' no projeto '{proj_title}'.",
            link=f"/kanban/projetos/{card.project_id}?card={card.id}"
        )
    await db.commit()

async def notify_attachment_added(
    db: AsyncSession,
    card: KanbanCard,
    attachment_name: str,
    author: User
):
    """Notify project participants and card assignees when an attachment is added."""
    autor_nome = author.nome if author else "Um participante"
    
    proj_title = "Projeto"
    project = None
    if card and card.project_id:
        stmt = select(KanbanProject).options(selectinload(KanbanProject.participantes)).where(KanbanProject.id == card.project_id)
        res = await db.execute(stmt)
        project = res.scalars().first()
        if project:
            proj_title = project.titulo
    
    recipients = set()
    if project and project.participantes:
        for p in project.participantes:
            recipients.add(p.id)
    if project and project.criador_id:
        recipients.add(project.criador_id)
    if card.participantes:
        for p in card.participantes:
            recipients.add(p.id)
    if card.responsavel_id:
        recipients.add(card.responsavel_id)
    
    if author and author.id in recipients:
        recipients.remove(author.id)

    for uid in recipients:
        await create_kanban_notification(
            db=db,
            user_id=uid,
            project_id=card.project_id,
            card_id=card.id,
            autor_id=author.id if author else None,
            tipo="ANEXO_ADICIONADO",
            titulo=f"Novo Anexo no Cartão: {card.titulo}",
            mensagem=f"{autor_nome} adicionou o anexo '{attachment_name}' no cartão '{card.titulo}'.",
            link=f"/kanban/projetos/{card.project_id}?card={card.id}"
        )
    await db.commit()
