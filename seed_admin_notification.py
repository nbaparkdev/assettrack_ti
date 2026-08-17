# seed_admin_notification.py
import asyncio

from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.services import kanban_notification_service as notif_service


async def seed_welcome_notifs():
    async with AsyncSessionLocal() as db:
        admin_ids = await notif_service.get_admin_user_ids(db)
        for aid in admin_ids:
            # Check if user already has notifications
            stmt = select(notif_service.KanbanNotification).where(notif_service.KanbanNotification.user_id == aid)
            res = await db.execute(stmt)
            if not res.first():
                await notif_service.create_kanban_notification(
                    db=db,
                    user_id=aid,
                    tipo="PROJETO_ADICIONADO",
                    titulo="Sistema de Notificações Ativo",
                    mensagem="As notificações do Kanban para administradores estão ativas. Você receberá atualizações em tempo real aqui e no menu superior.",
                    link="/kanban"
                )
        await db.commit()

if __name__ == "__main__":
    asyncio.run(seed_welcome_notifs())
