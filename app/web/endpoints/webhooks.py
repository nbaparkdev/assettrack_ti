from fastapi import APIRouter, Request, Depends, Form, BackgroundTasks
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.database import get_db
from app.web.dependencies import get_current_user_from_cookie, get_admin_user_web
from app.models.webhook import Webhook, WebhookLog
import json
from datetime import datetime

router = APIRouter()

from fastapi.templating import Jinja2Templates
templates = Jinja2Templates(directory="app/templates")

# Eventos suportados (mesmo do service)
WEBHOOK_EVENTS = [
    "ASSET_CREATED",
    "ASSET_UPDATED",
    "ASSET_DELETED",
    "MAINTENANCE_REQUESTED",
    "EMERGENCY_ALERT_TRIGGERED",
    "KANBAN_CARD_MOVED",
    "PURCHASE_REQUEST_CREATED"
]

@router.get("/webhooks", response_class=HTMLResponse)
async def list_webhooks(
    request: Request,
    admin_user=Depends(get_admin_user_web),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Webhook).order_by(Webhook.id.desc()))
    webhooks = result.scalars().all()
    
    return templates.TemplateResponse("webhooks/index.html", {
        "request": request,
        "user": admin_user,
        "webhooks": webhooks,
        "title": "Gerenciar Webhooks"
    })

@router.get("/webhooks/new", response_class=HTMLResponse)
async def new_webhook_form(
    request: Request,
    admin_user=Depends(get_admin_user_web)
):
    return templates.TemplateResponse("webhooks/form.html", {
        "request": request,
        "user": admin_user,
        "webhook": None,
        "events": WEBHOOK_EVENTS,
        "title": "Novo Webhook"
    })

@router.post("/webhooks/new")
async def create_webhook(
    request: Request,
    nome: str = Form(...),
    url: str = Form(...),
    is_active: bool = Form(True),
    admin_user=Depends(get_admin_user_web),
    db: AsyncSession = Depends(get_db)
):
    form_data = await request.form()
    eventos = form_data.getlist("eventos")
    
    novo = Webhook(
        nome=nome,
        url=url,
        is_active=is_active,
        eventos_permitidos=json.dumps(eventos)
    )
    db.add(novo)
    await db.commit()
    
    return RedirectResponse(url="/admin/webhooks", status_code=303)

@router.get("/webhooks/{webhook_id}/edit", response_class=HTMLResponse)
async def edit_webhook_form(
    webhook_id: int,
    request: Request,
    admin_user=Depends(get_admin_user_web),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Webhook).filter(Webhook.id == webhook_id))
    webhook = result.scalars().first()
    if not webhook:
        return RedirectResponse(url="/admin/webhooks")
        
    eventos_selecionados = json.loads(webhook.eventos_permitidos) if webhook.eventos_permitidos else []
    
    return templates.TemplateResponse("webhooks/form.html", {
        "request": request,
        "user": admin_user,
        "webhook": webhook,
        "events": WEBHOOK_EVENTS,
        "eventos_selecionados": eventos_selecionados,
        "title": "Editar Webhook"
    })

@router.post("/webhooks/{webhook_id}/edit")
async def update_webhook(
    webhook_id: int,
    request: Request,
    nome: str = Form(...),
    url: str = Form(...),
    is_active: bool = Form(False), # Fallback if checkbox is unchecked
    admin_user=Depends(get_admin_user_web),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Webhook).filter(Webhook.id == webhook_id))
    webhook = result.scalars().first()
    if not webhook:
        return RedirectResponse(url="/admin/webhooks")
        
    form_data = await request.form()
    eventos = form_data.getlist("eventos")
    
    webhook.nome = nome
    webhook.url = url
    # Checkbox 'is_active' only comes in form data if checked
    webhook.is_active = "is_active" in form_data
    webhook.eventos_permitidos = json.dumps(eventos)
    
    await db.commit()
    return RedirectResponse(url="/admin/webhooks", status_code=303)

@router.post("/webhooks/{webhook_id}/delete")
async def delete_webhook(
    webhook_id: int,
    admin_user=Depends(get_admin_user_web),
    db: AsyncSession = Depends(get_db)
):
    await db.execute(delete(Webhook).where(Webhook.id == webhook_id))
    await db.commit()
    return RedirectResponse(url="/admin/webhooks", status_code=303)

@router.get("/webhooks/{webhook_id}/logs", response_class=HTMLResponse)
async def webhook_logs(
    webhook_id: int,
    request: Request,
    admin_user=Depends(get_admin_user_web),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Webhook).filter(Webhook.id == webhook_id))
    webhook = result.scalars().first()
    
    logs_result = await db.execute(select(WebhookLog).filter(WebhookLog.webhook_id == webhook_id).order_by(WebhookLog.id.desc()).limit(100))
    logs = logs_result.scalars().all()
    
    return templates.TemplateResponse("webhooks/logs.html", {
        "request": request,
        "user": admin_user,
        "webhook": webhook,
        "logs": logs,
        "title": f"Logs Webhook: {webhook.nome}"
    })
