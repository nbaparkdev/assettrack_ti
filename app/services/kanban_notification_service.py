# app/services/kanban_notification_service.py
from typing import List, Optional, Set
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.kanban import KanbanNotification, KanbanProject, KanbanCard
from app.models.user import User, UserRole

async def get_admin_user_ids(db: AsyncSession) -> Set[int]:
    """Helper to fetch IDs of all active administrators and IT managers."""
    stmt = select(User.id).where(
        User.is_active == True,
        User.role.in_([UserRole.ADMIN, UserRole.GERENTE, UserRole.GERENTE_INFRA])
    )
    res = await db.execute(stmt)
    return set(res.scalars().all())

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
    """Helper to create and persist a Kanban notification/progress entry for a target user."""
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

async def get_project_recipients(db: AsyncSession, project_id: Optional[int] = None, extra_user_ids: Optional[List[int]] = None) -> Set[int]:
    """Collect all target recipient IDs: Project Creator + Project Participants + Administrators + Extra Users."""
    recipients = set(extra_user_ids or [])
    
    # Always include all active administrators and managers
    admin_ids = await get_admin_user_ids(db)
    recipients.update(admin_ids)

    if project_id:
        stmt = select(KanbanProject).options(selectinload(KanbanProject.participantes)).where(KanbanProject.id == project_id)
        res = await db.execute(stmt)
        project = res.scalars().first()
        if project:
            if project.criador_id:
                recipients.add(project.criador_id)
            if project.participantes:
                for p in project.participantes:
                    recipients.add(p.id)

    return recipients

async def notify_project_created(
    db: AsyncSession,
    project: KanbanProject,
    user_ids: List[int],
    author: User
):
    """Notify users and administrators when a new Kanban project is created."""
    autor_nome = author.nome if author else "Um usuário"
    proj_title = project.titulo if project else "Projeto"
    proj_id = project.id if project else None

    recipients = await get_project_recipients(db, proj_id, user_ids)

    for uid in recipients:
        await create_kanban_notification(
            db=db,
            user_id=uid,
            project_id=proj_id,
            autor_id=author.id if author else None,
            tipo="PROJETO_ADICIONADO",
            titulo=f"Novo Projeto: {proj_title}",
            mensagem=f"{autor_nome} criou o projeto '{proj_title}'.",
            link=f"/kanban/projetos/{proj_id}" if proj_id else "/kanban"
        )
    await db.commit()

async def notify_project_updated(
    db: AsyncSession,
    project: KanbanProject,
    author: User
):
    """Notify users and administrators when project details are updated."""
    autor_nome = author.nome if author else "Um usuário"
    proj_title = project.titulo if project else "Projeto"

    recipients = await get_project_recipients(db, project.id)

    for uid in recipients:
        await create_kanban_notification(
            db=db,
            user_id=uid,
            project_id=project.id,
            autor_id=author.id if author else None,
            tipo="PROJETO_ADICIONADO",
            titulo=f"Projeto Atualizado: {proj_title}",
            mensagem=f"{autor_nome} alterou as configurações do projeto '{proj_title}'.",
            link=f"/kanban/projetos/{project.id}"
        )
    await db.commit()

async def notify_card_created(
    db: AsyncSession,
    card: KanbanCard,
    author: User
):
    """Notify project participants, assignees, and administrators when a new card is created."""
    autor_nome = author.nome if author else "Um usuário"
    
    proj_title = "Projeto"
    if card and card.project_id:
        proj = await db.get(KanbanProject, card.project_id)
        if proj:
            proj_title = proj.titulo

    extra = []
    if card.responsavel_id:
        extra.append(card.responsavel_id)
    if card.participantes:
        for p in card.participantes:
            extra.append(p.id)

    recipients = await get_project_recipients(db, card.project_id, extra)

    for uid in recipients:
        await create_kanban_notification(
            db=db,
            user_id=uid,
            project_id=card.project_id,
            card_id=card.id,
            autor_id=author.id if author else None,
            tipo="CARTAO_ATRIBUIDO",
            titulo=f"Novo Cartão: {card.titulo}",
            mensagem=f"{autor_nome} criou o cartão '{card.titulo}' no projeto '{proj_title}'.",
            link=f"/kanban/projetos/{card.project_id}?card={card.id}"
        )
    await db.commit()

async def notify_card_assigned(
    db: AsyncSession,
    card: KanbanCard,
    user_ids: List[int],
    author: User
):
    """Notify assigned users and administrators for card assignment."""
    autor_nome = author.nome if author else "Um usuário"
    
    proj_title = "Projeto"
    if card and card.project_id:
        proj = await db.get(KanbanProject, card.project_id)
        if proj:
            proj_title = proj.titulo

    recipients = await get_project_recipients(db, card.project_id, user_ids)

    for uid in recipients:
        await create_kanban_notification(
            db=db,
            user_id=uid,
            project_id=card.project_id,
            card_id=card.id,
            autor_id=author.id if author else None,
            tipo="CARTAO_ATRIBUIDO",
            titulo=f"Atribuído ao Cartão: {card.titulo}",
            mensagem=f"{autor_nome} atribuiu integrantes ao cartão '{card.titulo}' no projeto '{proj_title}'.",
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
    """Notify project participants, assignees, and administrators when a card moves columns."""
    if source_col_name == target_col_name:
        return
    
    autor_nome = author.nome if author else "Um participante"
    
    proj_title = "Projeto"
    if card and card.project_id:
        proj = await db.get(KanbanProject, card.project_id)
        if proj:
            proj_title = proj.titulo

    extra = []
    if card.responsavel_id:
        extra.append(card.responsavel_id)
    if card.participantes:
        for p in card.participantes:
            extra.append(p.id)

    recipients = await get_project_recipients(db, card.project_id, extra)

    target_lower = target_col_name.lower()
    if "concluid" in target_lower or "finaliz" in target_lower or "done" in target_lower:
        notif_titulo = f"Concluído: {card.titulo}"
        notif_msg = f"{autor_nome} concluiu o cartão '{card.titulo}' (movido para '{target_col_name}') no projeto '{proj_title}'."
    else:
        notif_titulo = f"{target_col_name}: {card.titulo}"
        notif_msg = f"{autor_nome} moveu o cartão '{card.titulo}' de '{source_col_name}' para '{target_col_name}' no projeto '{proj_title}'."

    for uid in recipients:
        await create_kanban_notification(
            db=db,
            user_id=uid,
            project_id=card.project_id,
            card_id=card.id,
            autor_id=author.id if author else None,
            tipo="CARTAO_MOVIMENTADO",
            titulo=notif_titulo,
            mensagem=notif_msg,
            link=f"/kanban/projetos/{card.project_id}?card={card.id}"
        )
    await db.commit()

async def notify_card_updated(
    db: AsyncSession,
    card: KanbanCard,
    author: User
):
    """Notify project participants, assignees, and administrators when a card is edited."""
    autor_nome = author.nome if author else "Um usuário"
    
    proj_title = "Projeto"
    if card and card.project_id:
        proj = await db.get(KanbanProject, card.project_id)
        if proj:
            proj_title = proj.titulo

    extra = []
    if card.responsavel_id:
        extra.append(card.responsavel_id)
    if card.participantes:
        for p in card.participantes:
            extra.append(p.id)

    recipients = await get_project_recipients(db, card.project_id, extra)

    for uid in recipients:
        await create_kanban_notification(
            db=db,
            user_id=uid,
            project_id=card.project_id,
            card_id=card.id,
            autor_id=author.id if author else None,
            tipo="CARTAO_MOVIMENTADO",
            titulo=f"Cartão Atualizado: {card.titulo}",
            mensagem=f"{autor_nome} alterou o cartão '{card.titulo}' no projeto '{proj_title}'.",
            link=f"/kanban/projetos/{card.project_id}?card={card.id}"
        )
    await db.commit()

async def notify_attachment_added(
    db: AsyncSession,
    card: KanbanCard,
    attachment_name: str,
    author: User
):
    """Notify project participants, assignees, and administrators when an attachment is added."""
    autor_nome = author.nome if author else "Um participante"
    
    proj_title = "Projeto"
    if card and card.project_id:
        proj = await db.get(KanbanProject, card.project_id)
        if proj:
            proj_title = proj.titulo

    extra = []
    if card.responsavel_id:
        extra.append(card.responsavel_id)
    if card.participantes:
        for p in card.participantes:
            extra.append(p.id)

    recipients = await get_project_recipients(db, card.project_id, extra)

    for uid in recipients:
        await create_kanban_notification(
            db=db,
            user_id=uid,
            project_id=card.project_id,
            card_id=card.id,
            autor_id=author.id if author else None,
            tipo="ANEXO_ADICIONADO",
            titulo=f"Novo Anexo: {card.titulo}",
            mensagem=f"{autor_nome} adicionou o anexo '{attachment_name}' no cartão '{card.titulo}'.",
            link=f"/kanban/projetos/{card.project_id}?card={card.id}"
        )
    await db.commit()

async def notify_purchase_request_created(
    db: AsyncSession,
    card: KanbanCard,
    purchase_num: str,
    author: User
):
    """Notify project team and administrators when a purchase request is created from a card."""
    autor_nome = author.nome if author else "Um usuário"
    proj_title = "Projeto"
    if card and card.project_id:
        proj = await db.get(KanbanProject, card.project_id)
        if proj:
            proj_title = proj.titulo

    recipients = await get_project_recipients(db, card.project_id)

    for uid in recipients:
        await create_kanban_notification(
            db=db,
            user_id=uid,
            project_id=card.project_id,
            card_id=card.id,
            autor_id=author.id if author else None,
            tipo="CARTAO_MOVIMENTADO",
            titulo=f"Solicitação de Compra: {card.titulo}",
            mensagem=f"{autor_nome} gerou a solicitação de compra #{purchase_num} vinculada ao cartão '{card.titulo}'.",
            link=f"/kanban/projetos/{card.project_id}?card={card.id}"
        )
    await db.commit()

async def notify_stock_linked(
    db: AsyncSession,
    card: KanbanCard,
    product_name: str,
    author: User
):
    """Notify project team and administrators when a stock material is linked to a card."""
    autor_nome = author.nome if author else "Um usuário"
    proj_title = "Projeto"
    if card and card.project_id:
        proj = await db.get(KanbanProject, card.project_id)
        if proj:
            proj_title = proj.titulo

    recipients = await get_project_recipients(db, card.project_id)

    for uid in recipients:
        await create_kanban_notification(
            db=db,
            user_id=uid,
            project_id=card.project_id,
            card_id=card.id,
            autor_id=author.id if author else None,
            tipo="CARTAO_MOVIMENTADO",
            titulo=f"Baixa de Estoque: {card.titulo}",
            mensagem=f"{autor_nome} vinculou o item '{product_name}' do estoque ao cartão '{card.titulo}'.",
            link=f"/kanban/projetos/{card.project_id}?card={card.id}"
        )
    await db.commit()

async def notify_card_comment(
    db: AsyncSession,
    card: KanbanCard,
    comment_text: str,
    author: User
):
    """Notify project participants, assignees, and administrators when a comment is added to a card timeline."""
    autor_nome = author.nome if author else "Um usuário"
    
    proj_title = "Projeto"
    if card and card.project_id:
        proj = await db.get(KanbanProject, card.project_id)
        if proj:
            proj_title = proj.titulo

    extra = []
    if card.responsavel_id:
        extra.append(card.responsavel_id)
    if card.participantes:
        for p in card.participantes:
            extra.append(p.id)

    recipients = await get_project_recipients(db, card.project_id, extra)
    
    if author and author.id in recipients:
        recipients.remove(author.id)

    snippet = comment_text[:60] + "..." if len(comment_text) > 60 else comment_text

    for uid in recipients:
        await create_kanban_notification(
            db=db,
            user_id=uid,
            project_id=card.project_id,
            card_id=card.id,
            autor_id=author.id if author else None,
            tipo="NOVA_INTERACAO",
            titulo=f"Novo Comentário: {card.titulo}",
            mensagem=f"{autor_nome} comentou no cartão '{card.titulo}': \"{snippet}\"",
            link=f"/kanban/projetos/{card.project_id}?card={card.id}"
        )
    await db.commit()
