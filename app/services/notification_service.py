# app/services/notification_service.py
from typing import List, Optional
from datetime import datetime
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

    async def notify_order_assigned(
        self,
        db: AsyncSession,
        order_id: int,
        order_code: str,
        technician_id: int,
        technician_email: str,
        asset_name: str,
        priority: str,
        data_agendada: Optional[datetime] = None
    ):
        """Notifica o técnico quando uma ordem de serviço é atribuída a ele"""
        from app.models.preventive_maintenance import MaintenanceNotification
        
        subject = f"🔧 Nova OS Atribuída: {order_code} - {priority.upper()}"
        data_str = data_agendada.strftime('%d/%m/%Y %H:%M') if data_agendada else "Não agendada"
        
        message = f"""
Você foi designado como responsável por uma nova Ordem de Serviço de manutenção.

📋 OS Código: {order_code}
💻 Equipamento/Ativo: {asset_name}
⚠️ Prioridade: {priority.upper()}
📅 Data Agendada: {data_str}

Acesse o módulo de Manutenção Preventiva para iniciar a execução desta ordem.
"""
        # Criar notificação persistente no banco de dados
        notification = MaintenanceNotification(
            order_id=order_id,
            usuario_id=technician_id,
            tipo="ATRIBUICAO",
            mensagem=f"Você foi designado para a OS {order_code} ({asset_name}) agendada para {data_str}."
        )
        db.add(notification)
        
        # Enviar e-mail de notificação
        try:
            await self.email_service.send_notification(
                email_to=technician_email,
                subject=subject,
                message=message
            )
        except Exception:
            pass # Previne falhas se o serviço de email não estiver ativo
            
        print(f"[NOTIFICATION] OS #{order_id} atribuída ao técnico ID {technician_id}")

    async def notify_order_completed(
        self,
        db: AsyncSession,
        order_id: int,
        order_code: str,
        technician_name: str,
        asset_name: str,
        custo_total: float
    ):
        """Notifica os administradores e gerentes que uma OS foi concluída"""
        from app.models.preventive_maintenance import MaintenanceNotification
        
        # Buscar gestores/admins
        managers = await self.get_staff_users(db, roles=[UserRole.ADMIN, UserRole.GERENTE])
        
        subject = f"✅ OS Concluída: {order_code} - {asset_name}"
        message = f"""
A Ordem de Serviço {order_code} foi concluída pelo técnico responsável.

📋 Código: {order_code}
💻 Equipamento: {asset_name}
👨‍🔧 Técnico: {technician_name}
💰 Custo Total: R$ {custo_total:.2f}

Acesse a plataforma para auditar os detalhes e materiais aplicados.
"""
        # Notificar gestores no banco e via e-mail
        for mgr in managers:
            notification = MaintenanceNotification(
                order_id=order_id,
                usuario_id=mgr.id,
                tipo="CONCLUSAO",
                mensagem=f"A OS {order_code} ({asset_name}) foi concluída por {technician_name}. Custo: R$ {custo_total:.2f}."
            )
            db.add(notification)
            
            try:
                await self.email_service.send_notification(
                    email_to=mgr.email,
                    subject=subject,
                    message=message
                )
            except Exception:
                pass
                
        print(f"[NOTIFICATION] OS #{order_id} de conclusão enviada para gestores")

    async def notify_order_overdue(
        self,
        db: AsyncSession,
        order_id: int,
        order_code: str,
        technician_id: Optional[int],
        technician_email: Optional[str],
        asset_name: str,
        data_agendada: datetime
    ):
        """Notifica sobre OS preventiva atrasada"""
        from app.models.preventive_maintenance import MaintenanceNotification
        
        subject = f"⚠️ ALERTA: OS Atrasada {order_code} - {asset_name}"
        data_str = data_agendada.strftime('%d/%m/%Y %H:%M')
        
        message = f"""
Atenção, a Ordem de Serviço {order_code} está vencida e ainda não foi iniciada.

📋 Código: {order_code}
💻 Equipamento: {asset_name}
📅 Vencimento original: {data_str}

Favor verificar com urgência a situação desta manutenção.
"""
        # Se houver técnico atribuído, notifica ele
        if technician_id and technician_email:
            notification = MaintenanceNotification(
                order_id=order_id,
                usuario_id=technician_id,
                tipo="ATRASO",
                mensagem=f"A OS {order_code} ({asset_name}) sob sua responsabilidade está vencida desde {data_str}."
            )
            db.add(notification)
            try:
                await self.email_service.send_notification(
                    email_to=technician_email,
                    subject=subject,
                    message=message
                )
            except Exception:
                pass

        # Também notificar administradores e gerentes
        managers = await self.get_staff_users(db, roles=[UserRole.ADMIN, UserRole.GERENTE])
        for mgr in managers:
            notification = MaintenanceNotification(
                order_id=order_id,
                usuario_id=mgr.id,
                tipo="ATRASO_GESTOR",
                mensagem=f"ALERTA: A OS {order_code} ({asset_name}) está vencida desde {data_str}."
            )
            db.add(notification)
            try:
                await self.email_service.send_notification(
                    email_to=mgr.email,
                    subject=subject,
                    message=message
                )
            except Exception:
                pass
                
        print(f"[NOTIFICATION] OS #{order_id} de atraso gerada")


# Singleton
notification_service = NotificationService()
