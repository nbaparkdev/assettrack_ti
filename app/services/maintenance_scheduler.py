import asyncio
import logging
from datetime import datetime, timedelta
from app.core.datetime_utils import now_sp
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from app.database import SessionLocal
from app.models.preventive_maintenance import (
    MaintenancePlan, MaintenanceOrder, OrderStatus,
    MaintenanceType, MaintenancePriority, MaintenanceCriticality,
    MaintenancePeriodicity, MaintenanceHistory, MaintenancePlanAsset
)
from app.models.asset import Asset

logger = logging.getLogger("maintenance_scheduler")
logger.setLevel(logging.INFO)

# Configuração básica de log para a console se não estiver configurado
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

async def check_and_generate_preventive_orders():
    """
    Verifica planos de manutenção preventivos ativos que atingiram a data
    de próxima execução e gera as ordens de serviço correspondentes de forma idempootente.
    """
    logger.info("Iniciando verificação periódica de planos de manutenção preventivos...")
    
    async with SessionLocal() as db:
        try:
            # Buscar todos os planos ativos cuja próxima execução é hoje ou no passado
            now = now_sp()
            stmt = (
                select(MaintenancePlan)
                .options(
                    selectinload(MaintenancePlan.assets).selectinload(MaintenancePlanAsset.asset),
                    selectinload(MaintenancePlan.categoria)
                )
                .filter(MaintenancePlan.ativo == True)
                .filter(MaintenancePlan.proxima_execucao <= now)
            )
            result = await db.execute(stmt)
            plans = result.scalars().all()
            
            logger.info(f"Encontrados {len(plans)} planos de manutenção que precisam ser executados.")
            
            for plan in plans:
                # 1. Obter ativos qualificados para este plano
                assets_to_process = []
                
                # Caso o plano tenha ativos explicitamente vinculados
                if plan.assets:
                    assets_to_process = [pa.asset for pa in plan.assets if pa.asset]
                # Se não houver ativos diretos mas houver categoria especificada no plano,
                # aplica-se a todos os ativos daquela categoria
                elif plan.categoria_id:
                    asset_stmt = select(Asset).filter(Asset.categoria_id == plan.categoria_id)
                    asset_res = await db.execute(asset_stmt)
                    assets_to_process = asset_res.scalars().all()
                
                if not assets_to_process:
                    logger.warning(f"Plano {plan.codigo} não possui ativos vinculados ou categoria válida. Pulando...")
                    # Avançar a data de execução mesmo se não houver ativos para não travar o loop
                    await update_plan_next_execution(db, plan)
                    continue
                
                logger.info(f"Processando plano {plan.codigo} para {len(assets_to_process)} ativos.")
                
                orders_created_count = 0
                for asset in assets_to_process:
                    # 2. Evitar duplicação (idempotência - Opção A.1):
                    # Verificar se já existe uma OS aberta ou agendada para este plano, este ativo e data de abertura hoje
                    today_start = now_sp().replace(hour=0, minute=0, second=0, microsecond=0)
                    today_end = today_start + timedelta(days=1)
                    
                    dup_stmt = (
                        select(MaintenanceOrder)
                        .filter(MaintenanceOrder.plan_id == plan.id)
                        .filter(MaintenanceOrder.asset_id == asset.id)
                        .filter(MaintenanceOrder.data_abertura >= today_start)
                        .filter(MaintenanceOrder.data_abertura < today_end)
                        .filter(MaintenanceOrder.status.in_([
                            OrderStatus.ABERTA,
                            OrderStatus.AGENDADA,
                            OrderStatus.EM_ANDAMENTO,
                            OrderStatus.PAUSADA,
                            OrderStatus.AGUARDANDO_PECA
                        ]))
                    )
                    dup_res = await db.execute(dup_stmt)
                    existing_order = dup_res.scalar_one_or_none()
                    
                    if existing_order:
                        logger.info(f"Ordem de serviço já existe hoje para o plano {plan.codigo} e ativo {asset.nome} (OS: {existing_order.numero}). Pulando criação...")
                        continue
                    
                    # 3. Gerar número de OS único (OS-ANO-CONTAGEM)
                    year = now.year
                    count_stmt = (
                        select(func.count(MaintenanceOrder.id))
                        .filter(func.extract('year', MaintenanceOrder.data_abertura) == year)
                    )
                    count_res = await db.execute(count_stmt)
                    count = count_res.scalar() or 0
                    numero = f"OS-{year}-{count + 1 + orders_created_count:05d}"
                    
                    # 4. Criar a nova ordem de manutenção
                    desc = plan.descricao or ""
                    if not desc.strip():
                        desc = f"Ordem de manutenção gerada automaticamente a partir do plano {plan.nome} ({plan.codigo})."
                        
                    order = MaintenanceOrder(
                        numero=numero,
                        plan_id=plan.id,
                        asset_id=asset.id,
                        tecnico_id=plan.responsavel_id,
                        status=OrderStatus.ABERTA,
                        prioridade=plan.prioridade or MaintenancePriority.MEDIA,
                        criticidade=plan.criticidade or MaintenanceCriticality.MEDIA,
                        tipo=plan.tipo or MaintenanceType.PREVENTIVA,
                        observacoes=desc,
                        data_abertura=now_sp(),
                        data_agendada=now_sp()
                    )
                    db.add(order)
                    await db.flush() # Gerar ID temporário
                    
                    # Registrar no histórico da ordem
                    history = MaintenanceHistory(
                        order_id=order.id,
                        acao="Ordem Criada",
                        descricao="Ordem de serviço gerada automaticamente pelo sistema a partir do plano de manutenção.",
                        status_novo=OrderStatus.ABERTA.value
                    )
                    db.add(history)
                    
                    # Disparar notificação ao técnico designado no plano de manutenção
                    if plan.responsavel_id:
                        try:
                            from app.models.user import User
                            from app.services.notification_service import notification_service
                            
                            tech_stmt = select(User).filter(User.id == plan.responsavel_id)
                            tech_res = await db.execute(tech_stmt)
                            tech = tech_res.scalar_one_or_none()
                            
                            if tech:
                                await notification_service.notify_order_assigned(
                                    db=db,
                                    order_id=order.id,
                                    order_code=order.numero,
                                    technician_id=tech.id,
                                    technician_email=tech.email,
                                    asset_name=asset.nome,
                                    priority=order.prioridade.value,
                                    data_agendada=order.data_agendada
                                )
                        except Exception as ne:
                            logger.error(f"Erro ao notificar técnico designado pelo plano: {ne}")
                            
                    orders_created_count += 1
                
                # 5. Atualizar datas de execução do plano
                await update_plan_next_execution(db, plan)
                logger.info(f"Plano {plan.codigo} atualizado. {orders_created_count} novas ordens geradas.")
                
            await db.commit()
            logger.info("Verificação periódica concluída com sucesso.")
        except Exception as e:
            await db.rollback()
            logger.error(f"Erro ao processar a geração automática de ordens de serviço: {e}", exc_info=True)

async def update_plan_next_execution(db, plan: MaintenancePlan):
    """Calcula e atualiza a próxima data de execução de um plano de manutenção."""
    plan.data_ultima_execucao = now_sp()
    
    periodicity_days = {
        MaintenancePeriodicity.DIARIA: 1,
        MaintenancePeriodicity.SEMANAL: 7,
        MaintenancePeriodicity.QUINZENAL: 15,
        MaintenancePeriodicity.MENSAL: 30,
        MaintenancePeriodicity.BIMESTRAL: 60,
        MaintenancePeriodicity.TRIMESTRAL: 90,
        MaintenancePeriodicity.SEMESTRAL: 180,
        MaintenancePeriodicity.ANUAL: 365,
    }
    
    days = periodicity_days.get(plan.periodicidade, plan.dias_personalizado or 30)
    plan.proxima_execucao = now_sp() + timedelta(days=days)
    db.add(plan)

async def check_and_notify_overdue_orders():
    """
    Verifica ordens de serviço ativas (Abertas, Agendadas ou Pausadas) que estão
    atrasadas (data_agendada menor que hoje) e dispara notificações aos responsáveis e gestores.
    """
    logger.info("Iniciando verificação de ordens de serviço atrasadas...")
    async with SessionLocal() as db:
        try:
            from app.models.preventive_maintenance import MaintenanceNotification
            from app.services.notification_service import notification_service
            
            now = now_sp()
            
            # Buscar ordens de serviço não concluídas/canceladas com data agendada no passado
            stmt = (
                select(MaintenanceOrder)
                .options(
                    selectinload(MaintenanceOrder.asset),
                    selectinload(MaintenanceOrder.tecnico)
                )
                .filter(MaintenanceOrder.status.not_in([OrderStatus.CONCLUIDA, OrderStatus.CANCELADA]))
                .filter(MaintenanceOrder.data_agendada < now)
            )
            result = await db.execute(stmt)
            overdue_orders = result.scalars().all()
            
            logger.info(f"Encontradas {len(overdue_orders)} ordens de serviço atrasadas.")
            
            for order in overdue_orders:
                # Verificar se já não notificamos sobre atraso hoje para evitar spam
                today_start = now_sp().replace(hour=0, minute=0, second=0, microsecond=0)
                
                notif_stmt = (
                    select(func.count(MaintenanceNotification.id))
                    .filter(MaintenanceNotification.order_id == order.id)
                    .filter(MaintenanceNotification.tipo.in_(["ATRASO", "ATRASO_GESTOR"]))
                    .filter(MaintenanceNotification.data_criacao >= today_start)
                )
                notif_res = await db.execute(notif_stmt)
                already_notified_today = notif_res.scalar() or 0
                
                if already_notified_today > 0:
                    continue
                
                # Se não foi notificado hoje, notificar
                tech_id = order.tecnico_id
                tech_email = order.tecnico.email if order.tecnico else None
                asset_name = order.asset.nome if order.asset else (order.infra_predial_servico or "Infra Predial")
                
                await notification_service.notify_order_overdue(
                    db=db,
                    order_id=order.id,
                    order_code=order.numero,
                    technician_id=tech_id,
                    technician_email=tech_email,
                    asset_name=asset_name,
                    data_agendada=order.data_agendada
                )
            
            await db.commit()
            logger.info("Notificação de ordens atrasadas concluída.")
        except Exception as e:
            await db.rollback()
            logger.error(f"Erro ao verificar ou notificar ordens atrasadas: {e}", exc_info=True)


async def start_maintenance_scheduler_loop(interval_seconds: int = 3600):
    """
    Loop infinito de background para execução periódica da tarefa de geração e notificações de atraso.
    Default: verifica a cada 1 hora (3600 segundos).
    """
    logger.info("Iniciando loop do agendador de manutenção preventiva...")
    while True:
        try:
            await check_and_generate_preventive_orders()
            await check_and_notify_overdue_orders()
        except Exception as e:
            logger.error(f"Erro no loop do agendador de manutenção: {e}", exc_info=True)
        await asyncio.sleep(interval_seconds)
