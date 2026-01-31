# app/services/notification_service.py
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User, UserRole
from app.services.email_service import EmailService


class NotificationService:
    """Serviço para enviar notificações aos usuários relevantes"""
    
    def __init__(self):
        self.email_service = EmailService()
    
    async def get_staff_users(
        self, 
        db: AsyncSession, 
        roles: Optional[List[UserRole]] = None
    ) -> List[User]:
        """Busca usuários com roles de staff (técnico, gerente, admin)"""
        if roles is None:
            roles = [UserRole.TECNICO, UserRole.GERENTE, UserRole.ADMIN]
        
        result = await db.execute(
            select(User).filter(
                User.role.in_(roles),
                User.is_active == True
            )
        )
        return result.scalars().all()
    
    async def notify_new_maintenance_request(
        self, 
        db: AsyncSession,
        request_id: int,
        asset_name: str,
        requester_name: str,
        priority: str,
        description: str
    ):
        """
        Notifica técnicos, gerentes e admins sobre nova solicitação de manutenção
        """
        staff_users = await self.get_staff_users(db)
        
        subject = f"🔧 Nova Solicitação de Manutenção #{request_id} - {priority.upper()}"
        
        message = f"""
Nova solicitação de manutenção recebida:

📋 ID: #{request_id}
💻 Equipamento: {asset_name}
👤 Solicitante: {requester_name}
⚠️ Prioridade: {priority.upper()}

📝 Descrição:
{description[:200]}{'...' if len(description) > 200 else ''}

Acesse o painel de solicitações para mais detalhes.
"""
        
        notified = []
        for user in staff_users:
            await self.email_service.send_notification(
                email_to=user.email,
                subject=subject,
                message=message
            )
            notified.append(user.email)
        
        print(f"[NOTIFICATION] Manutenção #{request_id} - {len(notified)} notificados: {notified}")
        return notified
    
    async def notify_request_accepted(
        self, 
        db: AsyncSession,
        request_id: int,
        requester_email: str,
        asset_name: str,
        technician_name: str,
        observation: Optional[str] = None
    ):
        """Notifica o solicitante que seu pedido foi aceito"""
        subject = f"✅ Solicitação #{request_id} Aceita - Manutenção Iniciada"
        
        message = f"""
Sua solicitação de manutenção foi aceita!

📋 ID: #{request_id}
💻 Equipamento: {asset_name}
👨‍🔧 Técnico Responsável: {technician_name}

{f'Observação: {observation}' if observation else ''}

A manutenção foi iniciada. Você receberá atualizações sobre o andamento.
"""
        
        await self.email_service.send_notification(
            email_to=requester_email,
            subject=subject,
            message=message
        )
        
        print(f"[NOTIFICATION] Aceita #{request_id} - notificado: {requester_email}")
        return requester_email
    
    async def notify_request_rejected(
        self, 
        db: AsyncSession,
        request_id: int,
        requester_email: str,
        asset_name: str,
        technician_name: str,
        reason: str
    ):
        """Notifica o solicitante que seu pedido foi rejeitado"""
        subject = f"❌ Solicitação #{request_id} Rejeitada"
        
        message = f"""
Sua solicitação de manutenção foi analisada e não pôde ser atendida no momento.

📋 ID: #{request_id}
💻 Equipamento: {asset_name}
👨‍🔧 Analisado por: {technician_name}

📝 Motivo:
{reason}

Caso discorde ou tenha dúvidas, entre em contato com a equipe de TI.
"""
        
        await self.email_service.send_notification(
            email_to=requester_email,
            subject=subject,
            message=message
        )
        
        print(f"[NOTIFICATION] Rejeitada #{request_id} - notificado: {requester_email}")
        return requester_email
    
    async def notify_delivery_completed(
        self,
        db: AsyncSession,
        request_id: int,
        asset_name: str,
        requester_name: str,
        technician_name: str,
        observation: Optional[str] = None
    ):
        """
        Notifica Gerentes e Admins que uma entrega foi realizada pelo técnico.
        """
        # Buscar admins e gerentes
        managers = await self.get_staff_users(db, roles=[UserRole.ADMIN, UserRole.GERENTE])
        
        subject = f"📦 Entrega Realizada - Solicitação #{request_id}"
        
        message = f"""
Uma entrega de equipamento foi confirmada pelo técnico.

📋 ID Solicitação: #{request_id}
💻 Equipamento: {asset_name}
👤 Solicitante (Recebedor): {requester_name}
👨‍🔧 Técnico (Entregador): {technician_name}

{f'Observação: {observation}' if observation else ''}

Esta solicitação mudou para status ENTREGUE/CONCLUÍDA.
"""
        
        notified = []
        for user in managers:
            await self.email_service.send_notification(
                email_to=user.email,
                subject=subject,
                message=message
            )
            notified.append(user.email)
            
        print(f"[NOTIFICATION] Entrega #{request_id} - {len(notified)} gerentes notificados: {notified}")
        return notified


# Singleton
notification_service = NotificationService()
