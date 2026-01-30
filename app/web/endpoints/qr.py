
# app/web/endpoints/qr.py
from typing import Annotated
from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import timedelta

from app.database import get_db
from app.crud import user as user_crud
from app.services.qr_service import QRService
from app.web.dependencies import get_active_user_web
from app.models.user import User, UserRole
from app.models.transaction import Solicitacao, Movimentacao
from app.models.maintenance import Manutencao
from app.api.v1.endpoints.auth import create_access_token
from app.config import settings
from starlette import status

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# ===== Scanner de QR de Usuários (Admin/Gerente) =====

@router.get("/scanner/usuario", response_class=HTMLResponse)
async def scanner_usuario_page(
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)]
):
    """Página de scanner de QR Code de usuários (restrito Admin/Gerente)"""
    # Verificar permissão
    if current_user.role not in [UserRole.ADMIN, UserRole.GERENTE]:
        raise HTTPException(
            status_code=403,
            detail="Apenas Admin e Gerente TI podem escanear QR de usuários"
        )
    
    return templates.TemplateResponse("scanner_usuario.html", {
        "request": request,
        "user": current_user
    })

@router.get("/meu-qrcode", response_class=HTMLResponse)
async def meu_qrcode_page(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_active_user_web)]
):
    """Página com QR Code e crachá digital do usuário"""
    # Auto-gera token se não existir
    if not current_user.qr_token:
        await user_crud.user.regenerate_qr_token(db, user_id=current_user.id)
        await db.refresh(current_user)
    
    qr_base64 = QRService.generate_qr_base64(current_user.qr_token)
    
    # Buscar nome do departamento
    departamento_nome = None
    if current_user.departamento_id:
        await db.refresh(current_user, ["departamento"])
        if current_user.departamento:
            departamento_nome = current_user.departamento.nome
    
    return templates.TemplateResponse("meu_qrcode.html", {
        "request": request,
        "user": current_user,
        "qr_base64": qr_base64,
        "departamento_nome": departamento_nome,
        "success_pin": request.query_params.get("success") == "pin_updated",
        "success_qr": request.query_params.get("success") == "qr_regenerated"
    })

@router.post("/meu-qrcode/regenerar", response_class=HTMLResponse)
async def regenerar_qr(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_active_user_web)]
):
    """Regenera o QR Code do usuário"""
    await user_crud.user.regenerate_qr_token(db, user_id=current_user.id)
    return RedirectResponse(url="/meu-qrcode?success=qr_regenerated", status_code=status.HTTP_302_FOUND)

@router.post("/meu-qrcode/pin", response_class=HTMLResponse)
async def set_pin(
    request: Request,
    pin: Annotated[str, Form()],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_active_user_web)]
):
    """Define ou atualiza o PIN do usuário"""
    try:
        await user_crud.user.set_pin(db, user_id=current_user.id, pin=pin)
        return RedirectResponse(url="/meu-qrcode?success=pin_updated", status_code=status.HTTP_302_FOUND)
    except ValueError as e:
        await db.refresh(current_user)
        qr_base64 = QRService.generate_qr_base64(current_user.qr_token) if current_user.qr_token else ""
        return templates.TemplateResponse("meu_qrcode.html", {
            "request": request,
            "user": current_user,
            "qr_base64": qr_base64,
            "departamento_nome": None,
            "error_pin": str(e)
        })

# ===== Login via QR Code =====

@router.get("/login/qr", response_class=HTMLResponse)
async def login_qr_page(request: Request):
    """Página de login via QR Code"""
    return templates.TemplateResponse("login_qr.html", {"request": request})

@router.post("/login/qr", response_class=HTMLResponse)
async def login_qr_submit(
    request: Request,
    qr_token: Annotated[str, Form()],
    pin: Annotated[str, Form()],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Processa login via QR Code + PIN"""
    user = await user_crud.user.get_by_qr_token(db, token=qr_token)
    
    if not user:
        return templates.TemplateResponse("login_qr.html", {
            "request": request,
            "error": "QR Code inválido ou expirado"
        })
    
    if not user.is_active:
        return templates.TemplateResponse("login_qr.html", {
            "request": request,
            "error": "Conta não está ativa"
        })
    
    if not user.pin_hash:
        return templates.TemplateResponse("login_qr.html", {
            "request": request,
            "error": "PIN não configurado. Faça login com email/senha e configure seu PIN."
        })
    
    if not user_crud.user.verify_pin(pin, user.pin_hash):
        return templates.TemplateResponse("login_qr.html", {
            "request": request,
            "error": "PIN incorreto"
        })
    
    # Login bem sucedido
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role.value},
        expires_delta=access_token_expires
    )
    
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    return response

# ===== Perfil Público via QR (Admin/Gerente) =====

@router.get("/usuario/{token}", response_class=HTMLResponse)
async def user_public_profile_page(
    request: Request,
    token: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_active_user_web)]
):
    """Página de perfil público do usuário após scan do QR (restrito Admin/Gerente)"""
    # Verificar permissão
    if current_user.role not in [UserRole.ADMIN, UserRole.GERENTE]:
        raise HTTPException(
            status_code=403,
            detail="Apenas Admin e Gerente TI podem consultar perfis via QR"
        )
    
    user = await user_crud.user.get_by_qr_token(db, token=token)
    if not user:
        return templates.TemplateResponse("user_public_profile.html", {
            "request": request,
            "current_user": current_user,
            "target_user": None,
            "error": "Usuário não encontrado"
        })
    
    # Buscar nome do departamento
    departamento_nome = None
    if user.departamento_id:
        await db.refresh(user, ["departamento"])
        if user.departamento:
            departamento_nome = user.departamento.nome
    
    # Buscar histórico de solicitações
    solicitacoes_result = await db.execute(
        select(Solicitacao)
        .filter(Solicitacao.solicitante_id == user.id)
        .order_by(Solicitacao.data_solicitacao.desc())
        .limit(10)
    )
    solicitacoes = solicitacoes_result.scalars().all()
    
    # Buscar histórico de movimentações
    movimentacoes_result = await db.execute(
        select(Movimentacao)
        .filter(
            (Movimentacao.de_user_id == user.id) | 
            (Movimentacao.para_user_id == user.id)
        )
        .order_by(Movimentacao.data.desc())
        .limit(10)
    )
    movimentacoes = movimentacoes_result.scalars().all()
    
    # Buscar histórico de manutenções
    manutencoes_result = await db.execute(
        select(Manutencao)
        .filter(
            (Manutencao.responsavel_id == user.id) | 
            (Manutencao.destino_user_id == user.id)
        )
        .order_by(Manutencao.data_abertura.desc())
        .limit(10)
    )
    manutencoes = manutencoes_result.scalars().all()
    
    return templates.TemplateResponse("user_public_profile.html", {
        "request": request,
        "current_user": current_user,
        "target_user": user,
        "departamento_nome": departamento_nome,
        "solicitacoes": solicitacoes,
        "movimentacoes": movimentacoes,
        "manutencoes": manutencoes
    })
