import json
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.webhook import Webhook, WebhookLog
import asyncio
from app.database import SessionLocal

WEBHOOK_EVENTS = [
    "ASSET_CREATED",
    "ASSET_UPDATED",
    "ASSET_DELETED",
    "MAINTENANCE_REQUESTED",
    "EMERGENCY_ALERT_TRIGGERED",
    "KANBAN_CARD_MOVED",
    "PURCHASE_REQUEST_CREATED"
]

async def dispatch_webhook_event(evento: str, payload: dict):
    """
    Sends a POST request to all active webhooks subscribed to the given event.
    Logs the attempt and outcome. This should run in a background task.
    """
    if evento not in WEBHOOK_EVENTS:
        return
        
    async with SessionLocal() as db:
        result = await db.execute(select(Webhook).filter(Webhook.is_active == True))
        webhooks = result.scalars().all()
        
        target_webhooks = []
        for w in webhooks:
            try:
                eventos_permitidos = json.loads(w.eventos_permitidos)
                if evento in eventos_permitidos:
                    target_webhooks.append(w)
            except:
                pass
                
        if not target_webhooks:
            return

        payload_str = json.dumps(payload)
        
        async with httpx.AsyncClient() as client:
            for w in target_webhooks:
                # Prepare log entry
                log_entry = WebhookLog(
                    webhook_id=w.id,
                    evento=evento,
                    payload_enviado=payload_str,
                    sucesso=False
                )
                db.add(log_entry)
                
                try:
                    response = await client.post(w.url, json=payload, timeout=10.0)
                    log_entry.status_code = response.status_code
                    log_entry.response_body = response.text[:2000] # Limit to 2000 chars
                    if 200 <= response.status_code < 300:
                        log_entry.sucesso = True
                except Exception as e:
                    log_entry.response_body = str(e)[:2000]
                    log_entry.status_code = 0
                    
                await db.commit()
