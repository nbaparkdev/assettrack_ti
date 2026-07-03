
from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from app.core.datetime_utils import now_sp

from app.api import dependencies
from app.crud import preventive_maintenance as pm_crud
from app.crud import asset as asset_crud
from app.schemas.preventive_maintenance import (
    MaintenancePlanCreate,
    MaintenancePlanUpdate,
    MaintenancePlanResponse,
    MaintenanceChecklistCreate,
    MaintenanceChecklistUpdate,
    MaintenanceChecklistResponse,
    MaintenanceChecklistItemCreate,
    MaintenanceChecklistItemUpdate,
    MaintenanceChecklistItemResponse,
    MaintenanceOrderCreate,
    MaintenanceOrderUpdate,
    MaintenanceOrderResponse,
    MaintenanceExecutionCreate,
    MaintenanceExecutionUpdate,
    MaintenanceExecutionResponse,
    MaintenanceMaterialCreate,
    MaintenanceMaterialUpdate,
    MaintenanceMaterialResponse,
    MaintenancePhotoCreate,
    MaintenancePhotoUpdate,
    MaintenancePhotoResponse,
    MaintenanceHistoryResponse,
    MaintenanceNotificationCreate,
    MaintenanceNotificationUpdate,
    MaintenanceNotificationResponse,
    DashboardStats,
    DashboardChartData,
    MaintenanceDashboardResponse
)
from app.database import get_db
from app.models.preventive_maintenance import OrderStatus, MaintenanceType

router = APIRouter()


# ============== Maintenance Plans ==============
@router.get("/plans", response_model=List[MaintenancePlanResponse])
async def read_maintenance_plans(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dependencies.User, Depends(dependencies.get_current_active_user)],
    skip: int = 0,
    limit: int = 100,
    active_only: Optional[bool] = None
):
    if active_only:
        return await pm_crud.maintenance_plan.get_active_plans(db)
    return await pm_crud.maintenance_plan.get_multi(db, skip=skip, limit=limit)


@router.get("/plans/{plan_id}", response_model=MaintenancePlanResponse)
async def read_maintenance_plan(
    plan_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dependencies.User, Depends(dependencies.get_current_active_user)]
):
    plan = await pm_crud.maintenance_plan.get(db, id=plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plano de manutenção não encontrado")
    return plan


@router.post("/plans", response_model=MaintenancePlanResponse)
async def create_maintenance_plan(
    plan_in: MaintenancePlanCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dependencies.User, Depends(dependencies.get_current_active_manager_or_superuser)]
):
    # Generate unique code
    codigo = await pm_crud.maintenance_plan.generate_codigo(db)
    
    # Create plan data
    plan_data = plan_in.model_dump(exclude={"asset_ids", "checklists"})
    plan_data["codigo"] = codigo
    
    # Create plan
    db_plan = await pm_crud.maintenance_plan.create(db, obj_in=plan_data)
    
    # Add assets if provided
    if plan_in.asset_ids:
        for asset_id in plan_in.asset_ids:
            await pm_crud.maintenance_plan_asset.create(
                db, obj_in={"plan_id": db_plan.id, "asset_id": asset_id}
            )
    
    # Add checklists if provided
    if plan_in.checklists:
        for checklist_in in plan_in.checklists:
            checklist_data = checklist_in.model_dump(exclude={"items"})
            checklist_data["plan_id"] = db_plan.id
            db_checklist = await pm_crud.maintenance_checklist.create(db, obj_in=checklist_data)
            
            if checklist_in.items:
                for item_in in checklist_in.items:
                    item_data = item_in.model_dump()
                    item_data["checklist_id"] = db_checklist.id
                    await pm_crud.maintenance_checklist_item.create(db, obj_in=item_data)
    
    await db.refresh(db_plan)
    return await pm_crud.maintenance_plan.get(db, id=db_plan.id)


@router.put("/plans/{plan_id}", response_model=MaintenancePlanResponse)
async def update_maintenance_plan(
    plan_id: int,
    plan_in: MaintenancePlanUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dependencies.User, Depends(dependencies.get_current_active_manager_or_superuser)]
):
    plan = await pm_crud.maintenance_plan.get(db, id=plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plano de manutenção não encontrado")
    return await pm_crud.maintenance_plan.update(db, db_obj=plan, obj_in=plan_in)


@router.delete("/plans/{plan_id}")
async def delete_maintenance_plan(
    plan_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dependencies.User, Depends(dependencies.get_current_active_superuser)]
):
    plan = await pm_crud.maintenance_plan.get(db, id=plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plano de manutenção não encontrado")
    await pm_crud.maintenance_plan.remove(db, id=plan_id)
    return {"message": "Plano de manutenção removido com sucesso"}


# ============== Maintenance Checklists ==============
@router.get("/plans/{plan_id}/checklists", response_model=List[MaintenanceChecklistResponse])
async def read_plan_checklists(
    plan_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dependencies.User, Depends(dependencies.get_current_active_user)]
):
    return await pm_crud.maintenance_checklist.get_by_plan(db, plan_id=plan_id)


@router.post("/checklists", response_model=MaintenanceChecklistResponse)
async def create_checklist(
    checklist_in: MaintenanceChecklistCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dependencies.User, Depends(dependencies.get_current_active_manager_or_superuser)]
):
    return await pm_crud.maintenance_checklist.create(db, obj_in=checklist_in)


@router.put("/checklists/{checklist_id}", response_model=MaintenanceChecklistResponse)
async def update_checklist(
    checklist_id: int,
    checklist_in: MaintenanceChecklistUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dependencies.User, Depends(dependencies.get_current_active_manager_or_superuser)]
):
    checklist = await pm_crud.maintenance_checklist.get(db, id=checklist_id)
    if not checklist:
        raise HTTPException(status_code=404, detail="Checklist não encontrado")
    return await pm_crud.maintenance_checklist.update(db, db_obj=checklist, obj_in=checklist_in)


@router.delete("/checklists/{checklist_id}")
async def delete_checklist(
    checklist_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dependencies.User, Depends(dependencies.get_current_active_superuser)]
):
    checklist = await pm_crud.maintenance_checklist.get(db, id=checklist_id)
    if not checklist:
        raise HTTPException(status_code=404, detail="Checklist não encontrado")
    await pm_crud.maintenance_checklist.remove(db, id=checklist_id)
    return {"message": "Checklist removido com sucesso"}


# ============== Maintenance Checklist Items ==============
@router.get("/checklists/{checklist_id}/items", response_model=List[MaintenanceChecklistItemResponse])
async def read_checklist_items(
    checklist_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dependencies.User, Depends(dependencies.get_current_active_user)]
):
    return await pm_crud.maintenance_checklist_item.get_by_checklist(db, checklist_id=checklist_id)


@router.post("/checklist-items", response_model=MaintenanceChecklistItemResponse)
async def create_checklist_item(
    item_in: MaintenanceChecklistItemCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dependencies.User, Depends(dependencies.get_current_active_manager_or_superuser)]
):
    return await pm_crud.maintenance_checklist_item.create(db, obj_in=item_in)


@router.put("/checklist-items/{item_id}", response_model=MaintenanceChecklistItemResponse)
async def update_checklist_item(
    item_id: int,
    item_in: MaintenanceChecklistItemUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dependencies.User, Depends(dependencies.get_current_active_manager_or_superuser)]
):
    item = await pm_crud.maintenance_checklist_item.get(db, id=item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item de checklist não encontrado")
    return await pm_crud.maintenance_checklist_item.update(db, db_obj=item, obj_in=item_in)


@router.delete("/checklist-items/{item_id}")
async def delete_checklist_item(
    item_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dependencies.User, Depends(dependencies.get_current_active_superuser)]
):
    item = await pm_crud.maintenance_checklist_item.get(db, id=item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item de checklist não encontrado")
    await pm_crud.maintenance_checklist_item.remove(db, id=item_id)
    return {"message": "Item de checklist removido com sucesso"}


# ============== Maintenance Orders ==============
@router.get("/orders", response_model=List[MaintenanceOrderResponse])
async def read_maintenance_orders(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dependencies.User, Depends(dependencies.get_current_active_user)],
    skip: int = 0,
    limit: int = 100,
    status: Optional[OrderStatus] = None,
    asset_id: Optional[int] = None,
    tecnico_id: Optional[int] = None
):
    if status:
        return await pm_crud.maintenance_order.get_by_status(db, status=status)
    if asset_id:
        return await pm_crud.maintenance_order.get_by_asset(db, asset_id=asset_id)
    if tecnico_id:
        return await pm_crud.maintenance_order.get_by_tecnico(db, tecnico_id=tecnico_id)
    return await pm_crud.maintenance_order.get_multi(db, skip=skip, limit=limit)


@router.get("/orders/{order_id}", response_model=MaintenanceOrderResponse)
async def read_maintenance_order(
    order_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dependencies.User, Depends(dependencies.get_current_active_user)]
):
    order = await pm_crud.maintenance_order.get(db, id=order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Ordem de serviço não encontrada")
    return order


@router.post("/orders", response_model=MaintenanceOrderResponse)
async def create_maintenance_order(
    order_in: MaintenanceOrderCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dependencies.User, Depends(dependencies.get_current_active_manager_or_superuser)]
):
    # Generate unique number
    numero = await pm_crud.maintenance_order.generate_numero(db)
    
    # Create order data
    order_data = order_in.model_dump()
    order_data["numero"] = numero
    order_data["solicitante_id"] = current_user.id
    
    # Create order
    db_order = await pm_crud.maintenance_order.create(db, obj_in=order_data)
    
    # Create history entry
    await pm_crud.maintenance_history.create(
        db,
        obj_in={
            "order_id": db_order.id,
            "acao": "Criação",
            "descricao": "Ordem de serviço criada",
            "usuario_id": current_user.id,
            "status_novo": OrderStatus.ABERTA
        }
    )
    
    await db.refresh(db_order)
    return await pm_crud.maintenance_order.get(db, id=db_order.id)


@router.put("/orders/{order_id}", response_model=MaintenanceOrderResponse)
async def update_maintenance_order(
    order_id: int,
    order_in: MaintenanceOrderUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dependencies.User, Depends(dependencies.get_current_active_manager_or_superuser)]
):
    order = await pm_crud.maintenance_order.get(db, id=order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Ordem de serviço não encontrada")
    
    status_anterior = order.status
    
    # Update order
    updated_order = await pm_crud.maintenance_order.update(db, db_obj=order, obj_in=order_in)
    
    # Create history entry if status changed
    if order_in.status and order_in.status != status_anterior:
        await pm_crud.maintenance_history.create(
            db,
            obj_in={
                "order_id": order_id,
                "acao": "Atualização de Status",
                "descricao": f"Status alterado de {status_anterior} para {order_in.status}",
                "usuario_id": current_user.id,
                "status_anterior": status_anterior,
                "status_novo": order_in.status
            }
        )
    
    return updated_order


@router.delete("/orders/{order_id}")
async def delete_maintenance_order(
    order_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dependencies.User, Depends(dependencies.get_current_active_superuser)]
):
    order = await pm_crud.maintenance_order.get(db, id=order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Ordem de serviço não encontrada")
    await pm_crud.maintenance_order.remove(db, id=order_id)
    return {"message": "Ordem de serviço removida com sucesso"}


# ============== Order Status Transitions ==============
@router.post("/orders/{order_id}/start", response_model=MaintenanceOrderResponse)
async def start_maintenance_order(
    order_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dependencies.User, Depends(dependencies.get_current_active_user)]
):
    order = await pm_crud.maintenance_order.get(db, id=order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Ordem de serviço não encontrada")
    
    status_anterior = order.status
    now = now_sp()
    
    # Update order
    await pm_crud.maintenance_order.update(
        db,
        db_obj=order,
        obj_in={
            "status": OrderStatus.EM_ANDAMENTO,
            "data_inicio": now,
            "tecnico_id": current_user.id
        }
    )
    
    # Create history entry
    await pm_crud.maintenance_history.create(
        db,
        obj_in={
            "order_id": order_id,
            "acao": "Início",
            "descricao": "Manutenção iniciada",
            "usuario_id": current_user.id,
            "status_anterior": status_anterior,
            "status_novo": OrderStatus.EM_ANDAMENTO
        }
    )
    
    return await pm_crud.maintenance_order.get(db, id=order_id)


@router.post("/orders/{order_id}/pause", response_model=MaintenanceOrderResponse)
async def pause_maintenance_order(
    order_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dependencies.User, Depends(dependencies.get_current_active_user)]
):
    order = await pm_crud.maintenance_order.get(db, id=order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Ordem de serviço não encontrada")
    
    status_anterior = order.status
    
    # Update order
    await pm_crud.maintenance_order.update(
        db,
        db_obj=order,
        obj_in={
            "status": OrderStatus.PAUSADA,
            "data_pausa": now_sp()
        }
    )
    
    # Create history entry
    await pm_crud.maintenance_history.create(
        db,
        obj_in={
            "order_id": order_id,
            "acao": "Pausa",
            "descricao": "Manutenção pausada",
            "usuario_id": current_user.id,
            "status_anterior": status_anterior,
            "status_novo": OrderStatus.PAUSADA
        }
    )
    
    return await pm_crud.maintenance_order.get(db, id=order_id)


@router.post("/orders/{order_id}/complete", response_model=MaintenanceOrderResponse)
async def complete_maintenance_order(
    order_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dependencies.User, Depends(dependencies.get_current_active_user)]
):
    order = await pm_crud.maintenance_order.get(db, id=order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Ordem de serviço não encontrada")
    
    status_anterior = order.status
    now = now_sp()
    
    # Calculate total time
    tempo_total_minutos = None
    if order.data_inicio:
        delta = now - order.data_inicio
        tempo_total_minutos = int(delta.total_seconds() / 60)
    
    # Calculate total cost from materials
    custo_total = 0.0
    materials = await pm_crud.maintenance_material.get_by_order(db, order_id=order_id)
    for material in materials:
        custo_total += float(material.valor_total)
    
    # Update order
    await pm_crud.maintenance_order.update(
        db,
        db_obj=order,
        obj_in={
            "status": OrderStatus.CONCLUIDA,
            "data_conclusao": now,
            "tempo_total_minutos": tempo_total_minutos,
            "custo_total": custo_total
        }
    )
    
    # Create history entry
    await pm_crud.maintenance_history.create(
        db,
        obj_in={
            "order_id": order_id,
            "acao": "Conclusão",
            "descricao": "Manutenção concluída",
            "usuario_id": current_user.id,
            "status_anterior": status_anterior,
            "status_novo": OrderStatus.CONCLUIDA
        }
    )
    
    return await pm_crud.maintenance_order.get(db, id=order_id)


# ============== Maintenance Executions ==============
@router.get("/orders/{order_id}/executions", response_model=List[MaintenanceExecutionResponse])
async def read_order_executions(
    order_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dependencies.User, Depends(dependencies.get_current_active_user)]
):
    return await pm_crud.maintenance_execution.get_by_order(db, order_id=order_id)


@router.post("/executions", response_model=MaintenanceExecutionResponse)
async def create_execution(
    execution_in: MaintenanceExecutionCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dependencies.User, Depends(dependencies.get_current_active_user)]
):
    execution_data = execution_in.model_dump()
    execution_data["executado_por_id"] = current_user.id
    execution_data["data_execucao"] = now_sp()
    return await pm_crud.maintenance_execution.create(db, obj_in=execution_data)


@router.put("/executions/{execution_id}", response_model=MaintenanceExecutionResponse)
async def update_execution(
    execution_id: int,
    execution_in: MaintenanceExecutionUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dependencies.User, Depends(dependencies.get_current_active_user)]
):
    execution = await pm_crud.maintenance_execution.get(db, id=execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execução não encontrada")
    
    update_data = execution_in.model_dump(exclude_unset=True)
    if execution_in.concluido is not None:
        update_data["executado_por_id"] = current_user.id
        update_data["data_execucao"] = now_sp()
    
    return await pm_crud.maintenance_execution.update(db, db_obj=execution, obj_in=update_data)


# ============== Maintenance Materials ==============
@router.get("/orders/{order_id}/materials", response_model=List[MaintenanceMaterialResponse])
async def read_order_materials(
    order_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dependencies.User, Depends(dependencies.get_current_active_user)]
):
    return await pm_crud.maintenance_material.get_by_order(db, order_id=order_id)


@router.post("/materials", response_model=MaintenanceMaterialResponse)
async def create_material(
    material_in: MaintenanceMaterialCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dependencies.User, Depends(dependencies.get_current_active_manager_or_superuser)]
):
    return await pm_crud.maintenance_material.create(db, obj_in=material_in)


@router.put("/materials/{material_id}", response_model=MaintenanceMaterialResponse)
async def update_material(
    material_id: int,
    material_in: MaintenanceMaterialUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dependencies.User, Depends(dependencies.get_current_active_manager_or_superuser)]
):
    material = await pm_crud.maintenance_material.get(db, id=material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Material não encontrado")
    return await pm_crud.maintenance_material.update(db, db_obj=material, obj_in=material_in)


@router.delete("/materials/{material_id}")
async def delete_material(
    material_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dependencies.User, Depends(dependencies.get_current_active_superuser)]
):
    material = await pm_crud.maintenance_material.get(db, id=material_id)
    if not material:
        raise HTTPException(status_code=404, detail="Material não encontrado")
    await pm_crud.maintenance_material.remove(db, id=material_id)
    return {"message": "Material removido com sucesso"}


# ============== Maintenance Photos ==============
@router.get("/orders/{order_id}/photos", response_model=List[MaintenancePhotoResponse])
async def read_order_photos(
    order_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dependencies.User, Depends(dependencies.get_current_active_user)]
):
    return await pm_crud.maintenance_photo.get_by_order(db, order_id=order_id)


@router.post("/photos", response_model=MaintenancePhotoResponse)
async def create_photo(
    photo_in: MaintenancePhotoCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dependencies.User, Depends(dependencies.get_current_active_user)]
):
    photo_data = photo_in.model_dump()
    photo_data["upload_por_id"] = current_user.id
    return await pm_crud.maintenance_photo.create(db, obj_in=photo_data)


# ============== Maintenance History ==============
@router.get("/orders/{order_id}/history", response_model=List[MaintenanceHistoryResponse])
async def read_order_history(
    order_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dependencies.User, Depends(dependencies.get_current_active_user)]
):
    return await pm_crud.maintenance_history.get_by_order(db, order_id=order_id)


# ============== Dashboard ==============
@router.get("/dashboard", response_model=MaintenanceDashboardResponse)
async def get_dashboard(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dependencies.User, Depends(dependencies.get_current_active_user)]
):
    # Get stats
    all_orders = await pm_crud.maintenance_order.get_multi(db, skip=0, limit=1000)
    overdue = await pm_crud.maintenance_order.get_overdue(db)
    today = await pm_crud.maintenance_order.get_today(db)
    this_week = await pm_crud.maintenance_order.get_this_week(db)
    
    # Count completed orders
    completed_count = sum(1 for o in all_orders if o.status == OrderStatus.CONCLUIDA)
    in_progress_count = sum(1 for o in all_orders if o.status == OrderStatus.EM_ANDAMENTO)
    
    # Get unavailable assets
    assets = await asset_crud.asset.get_multi(db, skip=0, limit=1000)
    unavailable_count = sum(1 for a in assets if a.status == "Manutenção")
    
    stats = DashboardStats(
        manutencoes_vencidas=len(overdue),
        manutencoes_hoje=len(today),
        manutencoes_semana=len(this_week),
        manutencoes_concluidas=completed_count,
        ordens_em_andamento=in_progress_count,
        equipamentos_indisponiveis=unavailable_count
    )
    
    # Build chart data (simplified)
    charts = DashboardChartData(
        preventiva_vs_corretiva={
            MaintenanceType.PREVENTIVA: sum(1 for o in all_orders if o.tipo == MaintenanceType.PREVENTIVA),
            MaintenanceType.CORRETIVA: sum(1 for o in all_orders if o.tipo == MaintenanceType.CORRETIVA),
        },
        status_ordens={},
        ordens_por_tecnico={},
        ordens_por_setor={},
        custos_mensais={},
        equipamentos_mais_manutencoes={}
    )
    
    # Populate status counts
    for status in OrderStatus:
        charts.status_ordens[status] = sum(1 for o in all_orders if o.status == status)
    
    return MaintenanceDashboardResponse(
        stats=stats,
        charts=charts,
        proximas_manutencoes=today + this_week[:10]
    )

