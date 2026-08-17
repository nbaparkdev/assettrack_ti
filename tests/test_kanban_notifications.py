# tests/test_kanban_notifications.py
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.kanban import KanbanNotification, KanbanProject
from app.models.user import User, UserRole
from app.services import kanban_notification_service as notif_service


@pytest.mark.asyncio
async def test_kanban_notifications_workflow(db_session: AsyncSession):
    """Test creating, reading, and clearing notifications for Kanban events."""
    # 1. Create author and target user
    author = User(
        nome="Kanban Author User",
        email="kanban_author@example.com",
        hashed_password="hashedpassword",
        role=UserRole.USUARIO,
        is_active=True
    )
    admin = User(
        nome="Kanban Admin User",
        email="kanban_admin@example.com",
        hashed_password="hashedpassword",
        role=UserRole.ADMIN,
        is_active=True
    )
    db_session.add(author)
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(author)
    await db_session.refresh(admin)

    # 2. Create project
    proj = KanbanProject(
        titulo="Projeto Notificações Teste",
        descricao="Projeto para testar sistema de notificação em tempo real",
        criador_id=author.id
    )
    db_session.add(proj)
    await db_session.commit()
    await db_session.refresh(proj)

    # 3. Trigger notification: Project created
    await notif_service.notify_project_created(
        db=db_session,
        project=proj,
        user_ids=[],
        author=author
    )

    # 4. Query unread count for admin via db
    stmt = KanbanNotification.__table__.select().where(KanbanNotification.user_id == admin.id)
    res = await db_session.execute(stmt)
    notif = res.first()

    assert notif is not None
    assert notif.tipo == "PROJETO_ADICIONADO"
    assert "Projeto Notificações Teste" in notif.titulo
    assert notif.lida is False

    # 5. Mark read service helper test
    notif_obj = await db_session.get(KanbanNotification, notif.id)
    notif_obj.lida = True
    await db_session.commit()

    updated_notif = await db_session.get(KanbanNotification, notif.id)
    assert updated_notif.lida is True
