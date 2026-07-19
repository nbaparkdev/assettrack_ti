# app/services/notification_service.py
from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User, UserRole
from app.services.email_service import EmailService


from app.crud.system_settings import system_settings

class NotificationService:
    """Serviço para enviar notificações aos usuários relevantes"""
    
    def __init__(self):
        self.email_service = EmailService()
        
    async def _is_enabled(self, db: AsyncSession, key: str) -> bool:
        """Verifica se uma notificação específica está habilitada nas configurações"""
        val = await system_settings.get_setting(db, key, "true")
        return val.lower() == "true"
    
    async def get_staff_users(
        self, 
        db: AsyncSession, 
        roles: Optional[List[UserRole]] = None
    ) -> List[User]:
        """Busca usuários com roles de staff (técnico, gerente, admin, gerente_infra)"""
        if roles is None:
            roles = [UserRole.TECNICO, UserRole.GERENTE, UserRole.ADMIN, UserRole.GERENTE_INFRA]
        
        result = await db.execute(
            select(User).filter(
                User.role.in_(roles),
                User.is_active == True,
                User.email != None,  # garante email preenchido
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
        if not await self._is_enabled(db, "notify_new_maintenance_request"):
            return []
            
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
            if not user.email or "@" not in user.email:
                continue
            await self.email_service.send_notification(
                email_to=user.email,
                subject=subject,
                message=message,
                db=db
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
        if not await self._is_enabled(db, "notify_maintenance_accepted"):
            return None
            
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
            message=message,
            db=db
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
        if not await self._is_enabled(db, "notify_maintenance_rejected"):
            return None
            
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
            message=message,
            db=db
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
        if not await self._is_enabled(db, "notify_maintenance_delivery"):
            return []
            
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
            if not user.email or "@" not in user.email:
                continue
            await self.email_service.send_notification(
                email_to=user.email,
                subject=subject,
                message=message,
                db=db
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
        
        # Enviar e-mail de notificação se habilitado
        if await self._is_enabled(db, "notify_order_assigned"):
            try:
                await self.email_service.send_notification(
                    email_to=technician_email,
                    subject=subject,
                    message=message,
                    db=db
                )
            except Exception as e:
                print(f"[NOTIFICATION][ERRO] notify_order_assigned — OS #{order_id} para {technician_email}: {e}")
            
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
        notify_email = await self._is_enabled(db, "notify_order_completed")
        for mgr in managers:
            notification = MaintenanceNotification(
                order_id=order_id,
                usuario_id=mgr.id,
                tipo="CONCLUSAO",
                mensagem=f"A OS {order_code} ({asset_name}) foi concluída por {technician_name}. Custo: R$ {custo_total:.2f}."
            )
            db.add(notification)
            
            if notify_email:
                try:
                    await self.email_service.send_notification(
                        email_to=mgr.email,
                        subject=subject,
                        message=message,
                        db=db
                    )
                except Exception as e:
                    print(f"[NOTIFICATION][ERRO] notify_order_completed — OS #{order_id} para {mgr.email}: {e}")
                
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
        notify_email = await self._is_enabled(db, "notify_order_overdue")
        
        # Se houver técnico atribuído, notifica ele
        if technician_id and technician_email:
            notification = MaintenanceNotification(
                order_id=order_id,
                usuario_id=technician_id,
                tipo="ATRASO",
                mensagem=f"A OS {order_code} ({asset_name}) sob sua responsabilidade está vencida desde {data_str}."
            )
            db.add(notification)
            if notify_email:
                try:
                    await self.email_service.send_notification(
                        email_to=technician_email,
                        subject=subject,
                        message=message,
                        db=db
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
            if notify_email:
                try:
                    await self.email_service.send_notification(
                        email_to=mgr.email,
                        subject=subject,
                        message=message,
                        db=db
                    )
                except Exception:
                    pass
                
        print(f"[NOTIFICATION] OS #{order_id} de atraso gerada")

    # ─────────────────────────────────────────────
    # NOVOS HANDLERS (antes existiam apenas como toggles)
    # ─────────────────────────────────────────────

    async def notify_new_user(
        self,
        db: AsyncSession,
        user_nome: str,
        user_email: str,
        user_role: str
    ):
        """Notifica admins e gerentes quando um novo usuário se cadastra (aguardando aprovação)."""
        if not await self._is_enabled(db, "notify_new_user"):
            return

        staff = await self.get_staff_users(db, roles=[UserRole.ADMIN, UserRole.GERENTE, UserRole.GERENTE_INFRA])
        subject = f"👤 Novo usuário aguardando aprovação: {user_nome}"
        message = f"""
Um novo usuário se cadastrou no sistema e aguarda aprovação do administrador.

👤 Nome: {user_nome}
📧 E-mail: {user_email}
🔖 Perfil solicitado: {user_role}

Acesse /admin/users para aprovar ou rejeitar o acesso.
"""
        for u in staff:
            try:
                await self.email_service.send_notification(
                    email_to=u.email, subject=subject, message=message, db=db
                )
            except Exception as e:
                print(f"[NOTIFICATION][ERRO] notify_new_user para {u.email}: {e}")

        print(f"[NOTIFICATION] Novo usuário '{user_nome}' — {len(staff)} gestores notificados")

    async def notify_purchase_request(
        self,
        db: AsyncSession,
        request_id: int,
        request_numero: str,
        solicitante_nome: str,
        urgencia: str,
        total_estimado: float
    ):
        """Notifica gestores e compradores sobre nova solicitação de compra."""
        if not await self._is_enabled(db, "notify_purchase_request"):
            return

        staff = await self.get_staff_users(
            db, roles=[UserRole.ADMIN, UserRole.GERENTE, UserRole.GERENTE_INFRA, UserRole.COMPRADOR]
        )
        subject = f"🛒 Nova Solicitação de Compra {request_numero} — {urgencia.upper()}"
        message = f"""
Nova solicitação de compra aguardando análise e aprovação.

📋 Número: {request_numero}
👤 Solicitante: {solicitante_nome}
⚠️ Urgência: {urgencia.upper()}
💰 Valor estimado: R$ {total_estimado:.2f}

Acesse /compras/solicitacoes/{request_id} para revisar e aprovar.
"""
        for u in staff:
            try:
                await self.email_service.send_notification(
                    email_to=u.email, subject=subject, message=message, db=db
                )
            except Exception as e:
                print(f"[NOTIFICATION][ERRO] notify_purchase_request para {u.email}: {e}")

        print(f"[NOTIFICATION] Solicitação {request_numero} — {len(staff)} notificados")

    async def notify_purchase_order(
        self,
        db: AsyncSession,
        order_id: int,
        order_numero: str,
        fornecedor_nome: str,
        valor_total: float
    ):
        """Notifica gestores e compradores quando um Pedido de Compra (PO) é emitido."""
        if not await self._is_enabled(db, "notify_purchase_order"):
            return

        staff = await self.get_staff_users(
            db, roles=[UserRole.ADMIN, UserRole.GERENTE, UserRole.GERENTE_INFRA, UserRole.COMPRADOR]
        )
        subject = f"📦 Pedido de Compra Emitido: {order_numero}"
        message = f"""
Um novo Pedido de Compra foi gerado automaticamente após seleção do fornecedor vencedor.

📋 Número PO: {order_numero}
🏢 Fornecedor: {fornecedor_nome}
💰 Valor Total: R$ {valor_total:.2f}

Acesse /compras/pedidos/{order_id} para acompanhar o status.
"""
        for u in staff:
            try:
                await self.email_service.send_notification(
                    email_to=u.email, subject=subject, message=message, db=db
                )
            except Exception as e:
                print(f"[NOTIFICATION][ERRO] notify_purchase_order para {u.email}: {e}")

        print(f"[NOTIFICATION] PO {order_numero} emitido — {len(staff)} notificados")

    async def notify_low_stock(
        self,
        db: AsyncSession,
        product_name: str,
        saldo_atual: float,
        unidade: str = "un"
    ):
        """Notifica compradores quando um material atinge estoque baixo (saldo < 5)."""
        if not await self._is_enabled(db, "notify_low_stock"):
            return

        compradores = await self.get_staff_users(
            db, roles=[UserRole.ADMIN, UserRole.COMPRADOR, UserRole.GERENTE, UserRole.GERENTE_INFRA]
        )
        subject = f"⚠️ Estoque Baixo: {product_name}"
        message = f"""
Atenção! Um material no almoxarifado atingiu nível crítico de estoque.

📦 Material: {product_name}
📊 Saldo Atual: {saldo_atual:.2f} {unidade}

Acesse /compras/estoque e crie uma nova solicitação de compra para reposição.
"""
        for u in compradores:
            try:
                await self.email_service.send_notification(
                    email_to=u.email, subject=subject, message=message, db=db
                )
            except Exception as e:
                print(f"[NOTIFICATION][ERRO] notify_low_stock para {u.email}: {e}")

        print(f"[NOTIFICATION] Estoque baixo: '{product_name}' ({saldo_atual}) — {len(compradores)} notificados")

    async def notify_rh_ready_asset(
        self,
        db: AsyncSession,
        solicitacao_id: int,
        asset_name: str,
        requester_name: str
    ):
        """Notifica equipe de RH que um ativo está pronto para termo de responsabilidade"""
        if not await self._is_enabled(db, "notify_rh_ready_asset"):
            return
            
        rh_users = await self.get_staff_users(db, roles=[UserRole.RH])
        if not rh_users:
            print(f"[NOTIFICATION] Nenhum usuário com perfil RH cadastrado/ativo para receber notificação da solicitação #{solicitacao_id}")
            return
            
        subject = f"📋 Termo de Responsabilidade Requerido: Solicitação #{solicitacao_id}"
        message = f"""
Olá equipe de RH,

Um equipamento de TI está pronto para entrega e requer a elaboração e assinatura do Termo de Responsabilidade.

📋 ID Solicitação: #{solicitacao_id}
💻 Equipamento: {asset_name}
👤 Colaborador Destinatário: {requester_name}

Acesse o portal do RH (/rh/termos) para redigir o termo, salvar e gerar o PDF para assinatura do colaborador.
"""
        notified = []
        for u in rh_users:
            if not u.email or "@" not in u.email:
                continue
            try:
                await self.email_service.send_notification(
                    email_to=u.email,
                    subject=subject,
                    message=message,
                    db=db
                )
                notified.append(u.email)
            except Exception as e:
                print(f"[NOTIFICATION][ERRO] notify_rh_ready_asset para {u.email}: {e}")

        print(f"[NOTIFICATION] Notificação de Termo RH da solicitação #{solicitacao_id} — {len(notified)} RH notificados: {notified}")



# Singleton
notification_service = NotificationService()


async def notify_new_user_registered(
    db, user_nome: str, user_email: str, user_role: str
):
    """Wrapper chamado por auth.py ao registrar novo usuário."""
    await notification_service.notify_new_user(db, user_nome, user_email, user_role)
