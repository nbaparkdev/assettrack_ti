
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.datetime_utils import now_sp
from app.crud.base import CRUDBase
from app.models.preventive_maintenance import (
    MaintenanceChecklist,
    MaintenanceChecklistItem,
    MaintenanceExecution,
    MaintenanceHistory,
    MaintenanceMaterial,
    MaintenanceNotification,
    MaintenanceOrder,
    MaintenancePhoto,
    MaintenancePlan,
    MaintenancePlanAsset,
    OrderStatus,
)
from app.schemas.preventive_maintenance import (
    MaintenanceChecklistCreate,
    MaintenanceChecklistItemCreate,
    MaintenanceChecklistItemUpdate,
    MaintenanceChecklistUpdate,
    MaintenanceExecutionCreate,
    MaintenanceExecutionUpdate,
    MaintenanceHistoryCreate,
    MaintenanceMaterialCreate,
    MaintenanceMaterialUpdate,
    MaintenanceNotificationCreate,
    MaintenanceNotificationUpdate,
    MaintenanceOrderCreate,
    MaintenanceOrderUpdate,
    MaintenancePhotoCreate,
    MaintenancePhotoUpdate,
    MaintenancePlanAssetCreate,
    MaintenancePlanCreate,
    MaintenancePlanUpdate,
)


class CRUDMaintenancePlan(CRUDBase[MaintenancePlan, MaintenancePlanCreate, MaintenancePlanUpdate]):
    async def get(self, db: AsyncSession, id: int) -> MaintenancePlan | None:
        result = await db.execute(
            select(MaintenancePlan)
            .options(
                selectinload(MaintenancePlan.responsavel),
                selectinload(MaintenancePlan.departamento),
                selectinload(MaintenancePlan.categoria),
                selectinload(MaintenancePlan.assets).selectinload(MaintenancePlanAsset.asset),
                selectinload(MaintenancePlan.checklists).selectinload(MaintenanceChecklist.items)
            )
            .filter(MaintenancePlan.id == id)
        )
        return result.scalars().first()

    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> list[MaintenancePlan]:
        result = await db.execute(
            select(MaintenancePlan)
            .options(
                selectinload(MaintenancePlan.responsavel),
                selectinload(MaintenancePlan.departamento),
                selectinload(MaintenancePlan.categoria)
            )
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    async def get_by_codigo(self, db: AsyncSession, *, codigo: str) -> MaintenancePlan | None:
        result = await db.execute(
            select(MaintenancePlan)
            .options(
                selectinload(MaintenancePlan.responsavel),
                selectinload(MaintenancePlan.departamento),
                selectinload(MaintenancePlan.categoria)
            )
            .filter(MaintenancePlan.codigo == codigo)
        )
        return result.scalars().first()

    async def get_active_plans(self, db: AsyncSession) -> list[MaintenancePlan]:
        result = await db.execute(
            select(MaintenancePlan)
            .options(
                selectinload(MaintenancePlan.assets).selectinload(MaintenancePlanAsset.asset)
            )
            .filter(MaintenancePlan.ativo == True)
        )
        return result.scalars().all()

    async def generate_codigo(self, db: AsyncSession) -> str:
        import re
        now = now_sp()
        year = now.year
        prefix = f"PLAN-{year}-"
        result = await db.execute(
            select(MaintenancePlan.codigo)
            .filter(MaintenancePlan.codigo.like(f"{prefix}%"))
        )
        existing = set(result.scalars().all())
        
        max_seq = 0
        for cod in existing:
            match = re.search(r'PLAN-\d{4}-(\d+)', cod)
            if match:
                val = int(match.group(1))
                max_seq = max(max_seq, val)
                    
        seq = max(max_seq + 1, len(existing) + 1)
        while f"{prefix}{seq:05d}" in existing:
            seq += 1
            
        return f"{prefix}{seq:05d}"


class CRUDMaintenancePlanAsset(CRUDBase[MaintenancePlanAsset, MaintenancePlanAssetCreate, MaintenancePlanAssetCreate]):
    async def get_by_plan_and_asset(
        self, db: AsyncSession, *, plan_id: int, asset_id: int
    ) -> MaintenancePlanAsset | None:
        result = await db.execute(
            select(MaintenancePlanAsset)
            .filter(MaintenancePlanAsset.plan_id == plan_id)
            .filter(MaintenancePlanAsset.asset_id == asset_id)
        )
        return result.scalars().first()

    async def get_by_plan(self, db: AsyncSession, *, plan_id: int) -> list[MaintenancePlanAsset]:
        result = await db.execute(
            select(MaintenancePlanAsset)
            .options(selectinload(MaintenancePlanAsset.asset))
            .filter(MaintenancePlanAsset.plan_id == plan_id)
        )
        return result.scalars().all()


class CRUDMaintenanceChecklist(CRUDBase[MaintenanceChecklist, MaintenanceChecklistCreate, MaintenanceChecklistUpdate]):
    async def get(self, db: AsyncSession, id: int) -> MaintenanceChecklist | None:
        result = await db.execute(
            select(MaintenanceChecklist)
            .options(selectinload(MaintenanceChecklist.items))
            .filter(MaintenanceChecklist.id == id)
        )
        return result.scalars().first()

    async def get_by_plan(self, db: AsyncSession, *, plan_id: int) -> list[MaintenanceChecklist]:
        result = await db.execute(
            select(MaintenanceChecklist)
            .options(selectinload(MaintenanceChecklist.items))
            .filter(MaintenanceChecklist.plan_id == plan_id)
            .order_by(MaintenanceChecklist.ordem)
        )
        return result.scalars().all()


class CRUDMaintenanceChecklistItem(CRUDBase[MaintenanceChecklistItem, MaintenanceChecklistItemCreate, MaintenanceChecklistItemUpdate]):
    async def get_by_checklist(self, db: AsyncSession, *, checklist_id: int) -> list[MaintenanceChecklistItem]:
        result = await db.execute(
            select(MaintenanceChecklistItem)
            .filter(MaintenanceChecklistItem.checklist_id == checklist_id)
            .order_by(MaintenanceChecklistItem.ordem)
        )
        return result.scalars().all()


class CRUDMaintenanceOrder(CRUDBase[MaintenanceOrder, MaintenanceOrderCreate, MaintenanceOrderUpdate]):
    async def get(self, db: AsyncSession, id: int) -> MaintenanceOrder | None:
        result = await db.execute(
            select(MaintenanceOrder)
            .options(
                selectinload(MaintenanceOrder.plan),
                selectinload(MaintenanceOrder.asset),
                selectinload(MaintenanceOrder.tecnico),
                selectinload(MaintenanceOrder.solicitante),
                selectinload(MaintenanceOrder.executions)
                .selectinload(MaintenanceExecution.checklist_item),
                selectinload(MaintenanceOrder.executions)
                .selectinload(MaintenanceExecution.executado_por),
                selectinload(MaintenanceOrder.materials),
                selectinload(MaintenanceOrder.photos)
                .selectinload(MaintenancePhoto.upload_por),
                selectinload(MaintenanceOrder.history)
                .selectinload(MaintenanceHistory.usuario)
            )
            .filter(MaintenanceOrder.id == id)
        )
        return result.scalars().first()

    async def get_multi(
        self, db: AsyncSession, *, skip: int = 0, limit: int = 100
    ) -> list[MaintenanceOrder]:
        result = await db.execute(
            select(MaintenanceOrder)
            .options(
                selectinload(MaintenanceOrder.asset),
                selectinload(MaintenanceOrder.tecnico)
            )
            .offset(skip)
            .limit(limit)
            .order_by(MaintenanceOrder.data_abertura.desc())
        )
        return result.scalars().all()

    async def get_by_numero(self, db: AsyncSession, *, numero: str) -> MaintenanceOrder | None:
        result = await db.execute(
            select(MaintenanceOrder)
            .options(
                selectinload(MaintenanceOrder.asset),
                selectinload(MaintenanceOrder.tecnico)
            )
            .filter(MaintenanceOrder.numero == numero)
        )
        return result.scalars().first()

    async def get_by_asset(self, db: AsyncSession, *, asset_id: int) -> list[MaintenanceOrder]:
        result = await db.execute(
            select(MaintenanceOrder)
            .options(
                selectinload(MaintenanceOrder.asset),
                selectinload(MaintenanceOrder.tecnico)
            )
            .filter(MaintenanceOrder.asset_id == asset_id)
            .order_by(MaintenanceOrder.data_abertura.desc())
        )
        return result.scalars().all()

    async def get_by_tecnico(self, db: AsyncSession, *, tecnico_id: int) -> list[MaintenanceOrder]:
        result = await db.execute(
            select(MaintenanceOrder)
            .options(
                selectinload(MaintenanceOrder.asset),
                selectinload(MaintenanceOrder.tecnico)
            )
            .filter(MaintenanceOrder.tecnico_id == tecnico_id)
            .order_by(MaintenanceOrder.data_abertura.desc())
        )
        return result.scalars().all()

    async def get_by_status(self, db: AsyncSession, *, status: OrderStatus) -> list[MaintenanceOrder]:
        result = await db.execute(
            select(MaintenanceOrder)
            .options(
                selectinload(MaintenanceOrder.asset),
                selectinload(MaintenanceOrder.tecnico)
            )
            .filter(MaintenanceOrder.status == status)
            .order_by(MaintenanceOrder.data_abertura.desc())
        )
        return result.scalars().all()

    async def get_overdue(self, db: AsyncSession) -> list[MaintenanceOrder]:
        now = now_sp()
        result = await db.execute(
            select(MaintenanceOrder)
            .options(
                selectinload(MaintenanceOrder.asset),
                selectinload(MaintenanceOrder.tecnico)
            )
            .filter(MaintenanceOrder.status.in_([OrderStatus.ABERTA, OrderStatus.AGENDADA, OrderStatus.EM_ANDAMENTO]))
            .filter(MaintenanceOrder.data_agendada < now)
            .order_by(MaintenanceOrder.data_agendada)
        )
        return result.scalars().all()

    async def get_today(self, db: AsyncSession) -> list[MaintenanceOrder]:
        today = now_sp().date()
        tomorrow = today + timedelta(days=1)
        result = await db.execute(
            select(MaintenanceOrder)
            .options(
                selectinload(MaintenanceOrder.asset),
                selectinload(MaintenanceOrder.tecnico)
            )
            .filter(MaintenanceOrder.status.in_([OrderStatus.ABERTA, OrderStatus.AGENDADA, OrderStatus.EM_ANDAMENTO]))
            .filter(MaintenanceOrder.data_agendada >= today)
            .filter(MaintenanceOrder.data_agendada < tomorrow)
            .order_by(MaintenanceOrder.data_agendada)
        )
        return result.scalars().all()

    async def get_this_week(self, db: AsyncSession) -> list[MaintenanceOrder]:
        now = now_sp()
        week_start = now - timedelta(days=now.weekday())
        week_end = week_start + timedelta(days=7)
        result = await db.execute(
            select(MaintenanceOrder)
            .options(
                selectinload(MaintenanceOrder.asset),
                selectinload(MaintenanceOrder.tecnico)
            )
            .filter(MaintenanceOrder.status.in_([OrderStatus.ABERTA, OrderStatus.AGENDADA, OrderStatus.EM_ANDAMENTO]))
            .filter(MaintenanceOrder.data_agendada >= week_start)
            .filter(MaintenanceOrder.data_agendada < week_end)
            .order_by(MaintenanceOrder.data_agendada)
        )
        return result.scalars().all()

    async def generate_numero(self, db: AsyncSession) -> str:
        import re
        now = now_sp()
        year = now.year
        prefix = f"OS-{year}-"
        result = await db.execute(
            select(MaintenanceOrder.numero)
            .filter(MaintenanceOrder.numero.like(f"{prefix}%"))
        )
        existing = set(result.scalars().all())
        
        max_seq = 0
        for num in existing:
            match = re.search(r'OS-\d{4}-(\d+)', num)
            if match:
                val = int(match.group(1))
                max_seq = max(max_seq, val)
                    
        seq = max(max_seq + 1, len(existing) + 1)
        while f"{prefix}{seq:05d}" in existing:
            seq += 1
            
        return f"{prefix}{seq:05d}"


class CRUDMaintenanceExecution(CRUDBase[MaintenanceExecution, MaintenanceExecutionCreate, MaintenanceExecutionUpdate]):
    async def get_by_order(self, db: AsyncSession, *, order_id: int) -> list[MaintenanceExecution]:
        result = await db.execute(
            select(MaintenanceExecution)
            .options(
                selectinload(MaintenanceExecution.checklist_item),
                selectinload(MaintenanceExecution.executado_por)
            )
            .filter(MaintenanceExecution.order_id == order_id)
        )
        return result.scalars().all()


class CRUDMaintenanceMaterial(CRUDBase[MaintenanceMaterial, MaintenanceMaterialCreate, MaintenanceMaterialUpdate]):
    async def get_by_order(self, db: AsyncSession, *, order_id: int) -> list[MaintenanceMaterial]:
        result = await db.execute(
            select(MaintenanceMaterial)
            .filter(MaintenanceMaterial.order_id == order_id)
        )
        return result.scalars().all()


class CRUDMaintenancePhoto(CRUDBase[MaintenancePhoto, MaintenancePhotoCreate, MaintenancePhotoUpdate]):
    async def get_by_order(self, db: AsyncSession, *, order_id: int) -> list[MaintenancePhoto]:
        result = await db.execute(
            select(MaintenancePhoto)
            .options(selectinload(MaintenancePhoto.upload_por))
            .filter(MaintenancePhoto.order_id == order_id)
            .order_by(MaintenancePhoto.data_upload.desc())
        )
        return result.scalars().all()


class CRUDMaintenanceHistory(CRUDBase[MaintenanceHistory, MaintenanceHistoryCreate, MaintenanceHistoryCreate]):
    async def get_by_order(self, db: AsyncSession, *, order_id: int) -> list[MaintenanceHistory]:
        result = await db.execute(
            select(MaintenanceHistory)
            .options(selectinload(MaintenanceHistory.usuario))
            .filter(MaintenanceHistory.order_id == order_id)
            .order_by(MaintenanceHistory.data_hora.desc())
        )
        return result.scalars().all()


class CRUDMaintenanceNotification(CRUDBase[MaintenanceNotification, MaintenanceNotificationCreate, MaintenanceNotificationUpdate]):
    async def get_by_usuario(self, db: AsyncSession, *, usuario_id: int, unread_only: bool = False) -> list[MaintenanceNotification]:
        query = select(MaintenanceNotification).filter(MaintenanceNotification.usuario_id == usuario_id)
        if unread_only:
            query = query.filter(MaintenanceNotification.lida == False)
        query = query.order_by(MaintenanceNotification.data_criacao.desc())
        result = await db.execute(query)
        return result.scalars().all()


maintenance_plan = CRUDMaintenancePlan(MaintenancePlan)
maintenance_plan_asset = CRUDMaintenancePlanAsset(MaintenancePlanAsset)
maintenance_checklist = CRUDMaintenanceChecklist(MaintenanceChecklist)
maintenance_checklist_item = CRUDMaintenanceChecklistItem(MaintenanceChecklistItem)
maintenance_order = CRUDMaintenanceOrder(MaintenanceOrder)
maintenance_execution = CRUDMaintenanceExecution(MaintenanceExecution)
maintenance_material = CRUDMaintenanceMaterial(MaintenanceMaterial)
maintenance_photo = CRUDMaintenancePhoto(MaintenancePhoto)
maintenance_history = CRUDMaintenanceHistory(MaintenanceHistory)
maintenance_notification = CRUDMaintenanceNotification(MaintenanceNotification)

