# app/web/endpoints/alerts.py
from typing import Annotated
import asyncio
from fastapi import APIRouter, Request, Depends, Form, HTTPException, status
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.web.dependencies import get_active_user_web
from app.models.user import User, UserRole
from app.models.asset import Asset, AssetStatus
from app.models.emergency_alert import EmergencyAlert
from app.services.alert_broadcaster import alert_broadcaster
from app.services.email_service import EmailService

router = APIRouter(prefix="/emergencia", tags=["emergency-alerts"])
email_service = EmailService()

@router.post("/alertar", response_class=JSONResponse)
async def send_emergency_alert(
    request: Request,
    motivo: Annotated[str, Form(...)],
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Recebe o motivo do alerta acionado pelo usuário comum no dashboard,
    identifica o setor e ativos atribuídos, salva no banco e transmite via SSE em tempo real.
    """
    if not motivo or not motivo.strip():
        raise HTTPException(status_code=400, detail="O motivo do alerta não pode estar em branco.")

    # Carregar setor/departamento
    setor_str = "Não informado"
    if current_user.departamento_id:
        user_with_dept = await db.execute(
            select(User).options(selectinload(User.departamento)).filter(User.id == current_user.id)
        )
        u_dept = user_with_dept.scalar_one_or_none()
        if u_dept and u_dept.departamento:
            setor_str = u_dept.departamento.nome
    elif current_user.cargo:
        setor_str = current_user.cargo

    # Carregar ativo(s) vinculado(s) em uso
    assets_result = await db.execute(
        select(Asset).filter(Asset.current_user_id == current_user.id, Asset.status == AssetStatus.EM_USO)
    )
    my_assets = assets_result.scalars().all()
    if my_assets:
        ativo_str = ", ".join([f"{a.nome} ({a.e_patrimonio})" if a.e_patrimonio else a.nome for a in my_assets])
    else:
        ativo_str = "Nenhum ativo vinculado"

    # Salvar alerta no banco
    alert = EmergencyAlert(
        usuario_id=current_user.id,
        usuario_nome=current_user.nome,
        setor_nome=setor_str,
        ativo_nome=ativo_str,
        motivo=motivo.strip(),
        atendido=False
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)

    # Payload para transmissão em tempo real
    alert_payload = {
        "id": alert.id,
        "usuario_nome": current_user.nome,
        "usuario_id": current_user.id,
        "setor_nome": setor_str,
        "ativo_nome": ativo_str,
        "motivo": alert.motivo,
        "created_at": alert.created_at.strftime("%d/%m/%Y %H:%M:%S")
    }

    # Transmitir em tempo real via SSE
    await alert_broadcaster.broadcast(alert_payload)

    # Notificar emails da equipe (opcional / background)
    try:
        staff_result = await db.execute(
            select(User).filter(
                User.role.in_([UserRole.ADMIN, UserRole.GERENTE, UserRole.GERENTE_INFRA, UserRole.TECNICO]),
                User.is_active == True,
                User.email != None
            )
        )
        staff_members = staff_result.scalars().all()
        subject = f"🚨 ALERTA EMERGENCIAL: {current_user.nome} ({setor_str})"
        message = f"""
🚨 ALERTA DE EMERGÊNCIA EM TEMPO REAL

👤 Usuário: {current_user.nome}
🏢 Setor: {setor_str}
💻 Ativo: {ativo_str}
📅 Data/Hora: {alert_payload['created_at']}

📝 Motivo do Alerta:
{alert.motivo}

Acesse o sistema imediatamente para verificar a situação.
"""
        # Enviar e-mails em segundo plano sem bloquear a resposta HTTP do usuário
        async def _dispatch_emails(members, subj, msg):
            for staff in members:
                if staff.email and "@" in staff.email:
                    try:
                        await email_service.send_notification(
                            email_to=staff.email,
                            subject=subj,
                            message=msg,
                            db=db
                        )
                    except Exception:
                        pass

        asyncio.create_task(_dispatch_emails(staff_members, subject, message))
    except Exception as e:
        print(f"[EMERGENCY_ALERT] Erro ao agendar e-mails: {e}")

    return JSONResponse({
        "status": "success",
        "message": "Alerta emergencial transmitido aos administradores e equipe técnica!"
    })

@router.get("/stream")
async def emergency_alert_stream(
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)]
):
    """
    Stream de Server-Sent Events (SSE) para administradores, gerentes e técnicos
    receberem os alertas de emergência instantaneamente.
    """
    user_role = (current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)).lower()
    staff_roles = ['admin', 'gerente_ti', 'gerente_infra', 'tecnico', 'gerente']
    
    if user_role not in staff_roles:
        raise HTTPException(status_code=403, detail="Apenas administradores, gerentes e técnicos recebem a transmissão de emergência.")

    async def event_generator():
        queue = alert_broadcaster.subscribe()
        try:
            while True:
                # Se o cliente desconectou
                if await request.is_disconnected():
                    break
                try:
                    # Espera novo alerta com timeout para ping de keep-alive
                    payload = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield f"event: emergency_alert\ndata: {payload}\n\n"
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"
        finally:
            alert_broadcaster.unsubscribe(queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@router.get("/historico", response_class=JSONResponse)
async def get_emergency_history(
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Retorna o histórico de alertas emergenciais e contadores para equipe técnica/admin.
    """
    user_role = (current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)).lower()
    staff_roles = ['admin', 'gerente_ti', 'gerente_infra', 'tecnico', 'gerente']
    
    if user_role not in staff_roles:
        raise HTTPException(status_code=403, detail="Acesso negado.")

    res = await db.execute(
        select(EmergencyAlert)
        .options(selectinload(EmergencyAlert.atendido_por))
        .order_by(EmergencyAlert.created_at.desc())
        .limit(100)
    )
    alerts = res.scalars().all()

    total_count = len(alerts)
    pendentes_count = sum(1 for a in alerts if not a.atendido)

    data = []
    for a in alerts:
        atendido_por_nome = a.atendido_por.nome if (a.atendido and a.atendido_por) else "Sistema"
        data.append({
            "id": a.id,
            "usuario_nome": a.usuario_nome,
            "setor_nome": a.setor_nome or "Não informado",
            "ativo_nome": a.ativo_nome or "Nenhum ativo vinculado",
            "motivo": a.motivo,
            "atendido": a.atendido,
            "atendido_por_nome": atendido_por_nome if a.atendido else None,
            "created_at": a.created_at.strftime("%d/%m/%Y %H:%M:%S")
        })

    return JSONResponse({
        "total": total_count,
        "pendentes": pendentes_count,
        "alertas": data
    })

@router.post("/{alert_id}/atender", response_class=JSONResponse)
async def mark_emergency_alert_atendido(
    alert_id: int,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """
    Marca um alerta emergencial como atendido pelo administrador/técnico.
    """
    user_role = (current_user.role.value if hasattr(current_user.role, 'value') else str(current_user.role)).lower()
    staff_roles = ['admin', 'gerente_ti', 'gerente_infra', 'tecnico', 'gerente']
    
    if user_role not in staff_roles:
        raise HTTPException(status_code=403, detail="Acesso negado.")

    alert = await db.get(EmergencyAlert, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alerta não encontrado.")

    alert.atendido = True
    alert.atendido_por_id = current_user.id
    await db.commit()

    return JSONResponse({
        "status": "success",
        "message": f"Alerta #{alert_id} marcado como atendido por {current_user.nome}.",
        "atendido_por_nome": current_user.nome
    })
