# app/inspect_db.py
import asyncio
from app.database import SessionLocal
from app.models.preventive_maintenance import (
    MaintenanceExecution, MaintenancePhoto, MaintenanceOrder,
    MaintenanceChecklistItem, MaintenanceChecklist
)
from sqlalchemy import select

async def main():
    async with SessionLocal() as session:
        # Get order 3
        res_order = await session.execute(select(MaintenanceOrder).filter(MaintenanceOrder.id == 3))
        order = res_order.scalar_one_or_none()
        print(f"--- ORDER 3 ---")
        if order:
            print(f"ID: {order.id}, Plan ID: {order.plan_id}, Status: {order.status.value}")
        else:
            print("Order 3 not found")

        # Get checklists for order 3's plan
        if order and order.plan_id:
            res_ck = await session.execute(select(MaintenanceChecklist).filter(MaintenanceChecklist.plan_id == order.plan_id))
            checklists = res_ck.scalars().all()
            print("\n--- CHECKLISTS ---")
            for ck in checklists:
                print(f"Checklist ID: {ck.id}, Name: {ck.nome}")
                res_items = await session.execute(select(MaintenanceChecklistItem).filter(MaintenanceChecklistItem.checklist_id == ck.id))
                items = res_items.scalars().all()
                for item in items:
                    print(f"  Item ID: {item.id}, Description: {item.descricao}, Requer Foto: {item.requer_foto}")

        # Get executions
        res_exec = await session.execute(select(MaintenanceExecution))
        executions = res_exec.scalars().all()
        print("\n--- ALL EXECUTIONS ---")
        for e in executions:
            print(f"ID: {e.id}, Order ID: {e.order_id}, Checklist Item ID: {e.checklist_item_id}, Concluido: {e.concluido}")
            
        # Get photos
        res_photo = await session.execute(select(MaintenancePhoto))
        photos = res_photo.scalars().all()
        print("\n--- PHOTOS ---")
        for p in photos:
            print(f"ID: {p.id}, Order ID: {p.order_id}, Execution ID: {p.execution_id}, Caminho: {p.caminho_arquivo}")

if __name__ == "__main__":
    asyncio.run(main())
