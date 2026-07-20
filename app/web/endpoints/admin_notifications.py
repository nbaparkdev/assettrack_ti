from typing import Annotated
from fastapi import APIRouter, Request, Depends, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.database import get_db
from app.web.dependencies import get_admin_user_web
from app.models.user import User
from app.models.email_log import EmailLog
from app.crud.system_settings import system_settings

router = APIRouter(prefix="/admin/notificacoes", tags=["admin-notifications"], dependencies=[Depends(get_admin_user_web)])
templates = Jinja2Templates(directory="app/templates")

@router.get("", response_class=HTMLResponse)
async def admin_notifications_page(
    request: Request,
    current_user: Annotated[User, Depends(get_admin_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    # Fetch notification settings
    notify_new_user = await system_settings.get_setting(db, "notify_new_user", "true")
    notify_new_maintenance = await system_settings.get_setting(db, "notify_new_maintenance_request", "true")
    notify_maintenance_accepted = await system_settings.get_setting(db, "notify_maintenance_accepted", "true")
    notify_maintenance_rejected = await system_settings.get_setting(db, "notify_maintenance_rejected", "true")
    notify_maintenance_delivery = await system_settings.get_setting(db, "notify_maintenance_delivery", "true")
    notify_order_assigned = await system_settings.get_setting(db, "notify_order_assigned", "true")
    notify_order_completed = await system_settings.get_setting(db, "notify_order_completed", "true")
    notify_order_overdue = await system_settings.get_setting(db, "notify_order_overdue", "true")
    notify_purchase_request = await system_settings.get_setting(db, "notify_purchase_request", "true")
    notify_purchase_order = await system_settings.get_setting(db, "notify_purchase_order", "true")
    notify_low_stock = await system_settings.get_setting(db, "notify_low_stock", "true")

    success = request.query_params.get("success") == "1"

    # Fetch recent email logs
    logs_result = await db.execute(select(EmailLog).order_by(desc(EmailLog.sent_at)).limit(50))
    email_logs = logs_result.scalars().all()

    return templates.TemplateResponse("admin/notifications.html", {
        "request": request,
        "user": current_user,
        "success": success,
        "notify_new_user": notify_new_user == "true",
        "notify_new_maintenance": notify_new_maintenance == "true",
        "notify_maintenance_accepted": notify_maintenance_accepted == "true",
        "notify_maintenance_rejected": notify_maintenance_rejected == "true",
        "notify_maintenance_delivery": notify_maintenance_delivery == "true",
        "notify_order_assigned": notify_order_assigned == "true",
        "notify_order_completed": notify_order_completed == "true",
        "notify_order_overdue": notify_order_overdue == "true",
        "notify_purchase_request": notify_purchase_request == "true",
        "notify_purchase_order": notify_purchase_order == "true",
        "notify_low_stock": notify_low_stock == "true",
        "email_logs": email_logs,
        "title": "Configuração de Notificações"
    })

import logging

logger = logging.getLogger(__name__)

@router.post("")
async def admin_notifications_submit(
    request: Request,
    current_user: Annotated[User, Depends(get_admin_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    form_data = await request.form()
    
    # List of all configurable notifications
    notification_keys = [
        "notify_new_user",
        "notify_new_maintenance_request",
        "notify_maintenance_accepted",
        "notify_maintenance_rejected",
        "notify_maintenance_delivery",
        "notify_order_assigned",
        "notify_order_completed",
        "notify_order_overdue",
        "notify_purchase_request",
        "notify_purchase_order",
        "notify_low_stock"
    ]

    # Snapshot user attributes before any DB operation so the object
    # stays usable even if the session is rolled back / expired.
    user_snapshot = {
        "id": current_user.id,
        "nome": current_user.nome,
        "email": current_user.email,
        "role": current_user.role,
        "is_active": current_user.is_active,
        "avatar_url": getattr(current_user, "avatar_url", None),
    }

    try:
        for key in notification_keys:
            value = "true" if form_data.get(key) == "on" else "false"
            await system_settings.set_setting(db, key, value, commit=False)
        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.error(f"Erro ao salvar configurações de notificação: {e}")

        # Fetch email logs with a fresh query after rollback
        logs_result = await db.execute(select(EmailLog).order_by(desc(EmailLog.sent_at)).limit(50))
        email_logs = logs_result.scalars().all()

        return templates.TemplateResponse("admin/notifications.html", {
            "request": request,
            "user": user_snapshot,
            "error": f"Erro ao salvar configurações: {str(e)}",
            "notify_new_user": form_data.get("notify_new_user") == "on",
            "notify_new_maintenance": form_data.get("notify_new_maintenance_request") == "on",
            "notify_maintenance_accepted": form_data.get("notify_maintenance_accepted") == "on",
            "notify_maintenance_rejected": form_data.get("notify_maintenance_rejected") == "on",
            "notify_maintenance_delivery": form_data.get("notify_maintenance_delivery") == "on",
            "notify_order_assigned": form_data.get("notify_order_assigned") == "on",
            "notify_order_completed": form_data.get("notify_order_completed") == "on",
            "notify_order_overdue": form_data.get("notify_order_overdue") == "on",
            "notify_purchase_request": form_data.get("notify_purchase_request") == "on",
            "notify_purchase_order": form_data.get("notify_purchase_order") == "on",
            "notify_low_stock": form_data.get("notify_low_stock") == "on",
            "email_logs": email_logs,
            "title": "Configuração de Notificações"
        })

    return RedirectResponse(url="/admin/notificacoes?success=1", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/debug")
async def debug_email_logs(db: Annotated[AsyncSession, Depends(get_db)]):
    try:
        logs = await db.execute(select(EmailLog))
        log_list = logs.scalars().all()
        host = await system_settings.get_setting(db, "smtp_host", "NOT_FOUND")
        return {"logs": len(log_list), "smtp_host": host}
    except Exception as e:
        return {"error": str(e)}
