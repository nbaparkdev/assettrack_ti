
# app/api/v1/endpoints/qr.py
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from datetime import timedelta, datetime

from app.database import get_db
from app.api import dependencies
from app.crud import user as user_crud
from app.services.qr_service import QRService
from app.schemas.user import (
    UserQRResponse, 
    UserBadgeResponse, 
    PINSetupRequest, 
    QRLoginRequest,
    UserPublicProfile,
    DeliveryConfirmRequest,

    Token,
    PendingDeliveryItem
)
from app.models.user import User, UserRole
from app.models.transaction import Solicitacao, Movimentacao, StatusSolicitacao, TipoMovimentacao
from app.models.asset import Asset, AssetStatus
from app.models.maintenance_request import SolicitacaoManutencao, StatusSolicitacaoManutencao
from app.core.datetime_utils import now_sp
from app.api.v1.endpoints.auth import create_access_token
from app.config import settings
from app.core.rate_limit import limiter, get_rate_limit
from app.services.qr_log_service import QRLogService

# Token QR expira em 90 dias por padrão (configurável)
QR_TOKEN_EXPIRY_DAYS = 90

router = APIRouter()

def is_token_expired(created_at: datetime) -> bool:
    """Verifica se o token QR expirou"""
    if not created_at:
        return True
    expiry_date = created_at + timedelta(days=QR_TOKEN_EXPIRY_DAYS)
    return datetime.utcnow() > expiry_date

# ===== Endpoints para o próprio usuário =====

@router.post("/me/generate", response_model=UserQRResponse)
@limiter.limit(get_rate_limit("qr_regenerate"))
async def generate_qr_token(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(dependencies.get_current_active_user)]
):
    """Gera ou regenera o token QR do usuário logado"""
    new_token = await user_crud.user.regenerate_qr_token(db, user_id=current_user.id)
    qr_base64 = QRService.generate_qr_base64(new_token)
    
    # Registrar log de regeneração
    await QRLogService.log_regenerate(db, user_id=current_user.id, request=request)
    
    # Refresh user to get updated fields
    await db.refresh(current_user)
    
    return UserQRResponse(
        qr_code_base64=qr_base64,
        qr_token=new_token,
        created_at=current_user.qr_token_created_at,
        has_pin=current_user.pin_hash is not None
    )

@router.get("/me", response_model=UserQRResponse)
async def get_my_qr(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(dependencies.get_current_active_user)]
):
    """Retorna o QR Code atual do usuário (gera se não existir)"""
    if not current_user.qr_token:
        # Auto-gera token na primeira vez
        new_token = await user_crud.user.regenerate_qr_token(db, user_id=current_user.id)
        await db.refresh(current_user)
    
    qr_base64 = QRService.generate_qr_base64(current_user.qr_token)
    
    return UserQRResponse(
        qr_code_base64=qr_base64,
        qr_token=current_user.qr_token,
        created_at=current_user.qr_token_created_at,
        has_pin=current_user.pin_hash is not None
    )

@router.get("/me/badge", response_model=UserBadgeResponse)
async def get_my_badge(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(dependencies.get_current_active_user)]
):
    """Retorna dados para crachá digital do usuário"""
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
    
    return UserBadgeResponse(
        id=current_user.id,
        nome=current_user.nome,
        email=current_user.email,
        matricula=current_user.matricula,
        cargo=current_user.cargo,
        departamento_nome=departamento_nome,
        avatar_url=current_user.avatar_url,
        qr_code_base64=qr_base64
    )

@router.post("/me/pin")
@limiter.limit(get_rate_limit("pin_setup"))
async def set_user_pin(
    request: Request,
    pin_data: PINSetupRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(dependencies.get_current_active_user)]
):
    """Define ou atualiza PIN para login via QR Code"""
    had_pin = current_user.pin_hash is not None
    try:
        await user_crud.user.set_pin(db, user_id=current_user.id, pin=pin_data.pin)
        # Registrar log de configuração/alteração de PIN
        await QRLogService.log_pin_action(db, user_id=current_user.id, request=request, is_change=had_pin)
        return {"message": "PIN configurado com sucesso"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

# ===== Endpoint de Login via QR =====

@router.post("/login", response_model=Token)
@limiter.limit(get_rate_limit("qr_login"))
async def login_with_qr(
    request: Request,
    qr_data: QRLoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Login via QR Code + PIN"""
    user = await user_crud.user.get_by_qr_token(db, token=qr_data.qr_token)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="QR Code inválido ou expirado"
        )
    
    # Verificar se token expirou
    if is_token_expired(user.qr_token_created_at):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"QR Code expirado. Tokens expiram após {QR_TOKEN_EXPIRY_DAYS} dias. Regenere seu QR Code."
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Conta não está ativa"
        )
    
    if not user.pin_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="PIN não configurado. Configure o PIN no seu perfil."
        )
    
    if not user_crud.user.verify_pin(qr_data.pin, user.pin_hash):
        # Log de tentativa falha
        await QRLogService.log_login(db, user_id=user.id, request=request, success=False)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="PIN incorreto"
        )
    
    # Log de login bem sucedido
    await QRLogService.log_login(db, user_id=user.id, request=request, success=True)
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "role": user.role.value},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

# ===== Endpoint para consulta de perfil via QR (restrito Admin/Gerente) =====

@router.get("/user/{token}", response_model=UserPublicProfile)
async def get_user_by_qr(
    token: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(dependencies.get_current_active_user)]
):
    """
    Busca perfil público do usuário pelo token QR.
    Restrito a Admin e Gerente TI.
    """
    # Verificar permissão
    if current_user.role not in [UserRole.ADMIN, UserRole.GERENTE]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas Admin e Gerente TI podem consultar perfis via QR"
        )
    
    user = await user_crud.user.get_by_qr_token(db, token=token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    # Buscar nome do departamento
    departamento_nome = None
    if user.departamento_id:
        await db.refresh(user, ["departamento"])
        if user.departamento:
            departamento_nome = user.departamento.nome
    
    # Buscar Solicitacoes com Status APROVADA (Pendentes de Entrega)
    stmt_sol = select(Solicitacao).options(selectinload(Solicitacao.asset)).filter(
        Solicitacao.solicitante_id == user.id,
        Solicitacao.status == StatusSolicitacao.APROVADA
    )
    result_sol = await db.execute(stmt_sol)
    solicitacoes = result_sol.scalars().all()
    
    # Buscar Manutenções com Status AGUARDANDO_ENTREGA
    stmt_man = select(SolicitacaoManutencao).options(selectinload(SolicitacaoManutencao.asset)).filter(
        SolicitacaoManutencao.solicitante_id == user.id,
        SolicitacaoManutencao.status == StatusSolicitacaoManutencao.AGUARDANDO_ENTREGA
    )
    result_man = await db.execute(stmt_man)
    manutencoes = result_man.scalars().all()
    
    pending_items = []
    
    for s in solicitacoes:
        asset_tag = s.asset.serial_number if s.asset else "N/A"
        asset_nome = s.asset.nome if s.asset else "Ativo Solicitado"
        pending_items.append(PendingDeliveryItem(
            id=s.id,
            tipo="solicitacao",
            asset_tag=asset_tag,
            asset_nome=asset_nome,
            data_solicitacao=s.data_solicitacao,
            status=s.status.value
        ))

    for m in manutencoes:
        asset_tag = m.asset.serial_number if m.asset else "N/A"
        asset_nome = m.asset.nome if m.asset else "Ativo em Manutenção"
        pending_items.append(PendingDeliveryItem(
            id=m.id,
            tipo="manutencao",
            asset_tag=asset_tag,
            asset_nome=asset_nome,
            data_solicitacao=m.data_solicitacao,
            status=m.status.value
        ))
    
    return UserPublicProfile(
        id=user.id,
        nome=user.nome,
        email=user.email,
        matricula=user.matricula,
        cargo=user.cargo,
        departamento_nome=departamento_nome,
        avatar_url=user.avatar_url,
        pending_deliveries=pending_items
    )

# ===== Endpoint de Confirmação de Entrega =====

@router.post("/delivery/confirm")
async def confirm_delivery(
    data: DeliveryConfirmRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(dependencies.get_current_active_user)]
):
    """
    Confirma entrega de equipamento.
    - Admin/Gerente podem confirmar SEM QR (registra quem validou)
    - Técnico PRECISA do QR do usuário
    """
    # Verificar se é Admin/Gerente ou Técnico
    is_privileged = current_user.role in [UserRole.ADMIN, UserRole.GERENTE]
    
    # Se não for privileged, precisa do QR
    if not is_privileged and not data.qr_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="QR Code do usuário é obrigatório para técnicos"
        )
    
    # Validar usuário pelo QR (se fornecido)
    user_confirmador = None
    if data.qr_token:
        user_confirmador = await user_crud.user.get_by_qr_token(db, token=data.qr_token)
        if not user_confirmador:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="QR Code inválido"
            )
    
    # Processar confirmação de solicitação
    # Processar confirmação de solicitação
    if data.solicitacao_id:
        result = await db.execute(
            select(Solicitacao).options(selectinload(Solicitacao.asset)).filter(Solicitacao.id == data.solicitacao_id)
        )
        solicitacao = result.scalars().first()
        
        if not solicitacao:
            raise HTTPException(status_code=404, detail="Solicitação não encontrada")
        
        if solicitacao.status != StatusSolicitacao.APROVADA:
            raise HTTPException(status_code=400, detail="Solicitação não está aprovada")
        
        # Registrar observação de confirmação
        confirmado_por = user_confirmador.nome if user_confirmador else f"[VALIDAÇÃO MANUAL] {current_user.nome}"
        observacao_texto = f"Entrega confirmada por: {confirmado_por}"
        if data.observacao:
            observacao_texto += f" | Obs: {data.observacao}"
        
        # 1. Atualizar Status da Solicitação
        solicitacao.status = StatusSolicitacao.ENTREGUE
        solicitacao.data_entrega = now_sp()
        solicitacao.confirmado_por_id = current_user.id
        solicitacao.confirmado_via_qr = user_confirmador is not None
        solicitacao.observacao_entrega = observacao_texto
        
        # 2. Atualizar Status do Ativo e Responsável
        if solicitacao.asset:
            solicitacao.asset.status = AssetStatus.EM_USO
            solicitacao.asset.current_user_id = solicitacao.solicitante_id
            
            # Limpar outras localizações
            solicitacao.asset.current_departamento_id = None
            solicitacao.asset.current_local_id = None
            solicitacao.asset.current_armazenamento_id = None
        
        # 3. Criar log de Movimentação
        nova_movimentacao = Movimentacao(
            asset_id=solicitacao.asset_id,
            tipo=TipoMovimentacao.EMPRESTIMO,
            de_user_id=current_user.id, # Quem entregou (Técnico/Admin)
            para_user_id=solicitacao.solicitante_id,
            data=now_sp(),
            observacao=f"Entrega de solicitação #{solicitacao.id} confirmada via QR."
        )
        db.add(nova_movimentacao)
        
        await db.commit()
        await db.refresh(solicitacao)
        
        return {
            "message": "Entrega confirmada com sucesso",
            "confirmado_por": confirmado_por,
            "tipo": "solicitacao",
            "id": data.solicitacao_id,
            "validacao_manual": user_confirmador is None
        }

    # Processar confirmação de manutenção (retorno ao usuário)
    if data.manutencao_id:
        result = await db.execute(
            select(SolicitacaoManutencao).options(selectinload(SolicitacaoManutencao.asset)).filter(SolicitacaoManutencao.id == data.manutencao_id)
        )
        solicitacao_man = result.scalars().first()
        
        if not solicitacao_man:
            raise HTTPException(status_code=404, detail="Solicitação de manutenção não encontrada")
            
        if solicitacao_man.status != StatusSolicitacaoManutencao.AGUARDANDO_ENTREGA:
             raise HTTPException(status_code=400, detail="Manutenção não está aguardando entrega")

        # Registrar observação de confirmação
        confirmado_por = user_confirmador.nome if user_confirmador else f"[VALIDAÇÃO MANUAL] {current_user.nome}"
        observacao_texto = f"Devolução pós-manutenção confirmada por: {confirmado_por}"
        if data.observacao:
             observacao_texto += f" | Obs: {data.observacao}"

        # 1. Atualizar Status da Solicitação de Manutenção
        solicitacao_man.status = StatusSolicitacaoManutencao.CONCLUIDA
        solicitacao_man.data_entrega = now_sp()
        
        # 2. Atualizar Status do Ativo e Responsável
        if solicitacao_man.asset:
            solicitacao_man.asset.status = AssetStatus.EM_USO
            solicitacao_man.asset.current_user_id = solicitacao_man.solicitante_id
            
            # Limpar outras localizações
            solicitacao_man.asset.current_departamento_id = None
            solicitacao_man.asset.current_local_id = None
            solicitacao_man.asset.current_armazenamento_id = None

        # 3. Criar log de Movimentação (Devolução ao usuário)
        nova_movimentacao = Movimentacao(
            asset_id=solicitacao_man.asset_id,
            tipo=TipoMovimentacao.DEVOLUCAO, # ou TRANSFERENCIA, mas DEVOLUCAO faz sentido pós-manutenção
            de_user_id=current_user.id, # Quem entregou
            para_user_id=solicitacao_man.solicitante_id,
            data=now_sp(),
            observacao=f"Retorno de manutenção #{solicitacao_man.id} confirmada via QR."
        )
        db.add(nova_movimentacao)
        
        await db.commit()
        await db.refresh(solicitacao_man)

        return {
            "message": "Entrega confirmada com sucesso",
            "confirmado_por": confirmado_por,
            "tipo": "manutencao",
            "id": data.manutencao_id,
            "validacao_manual": user_confirmador is None
        }

    
    # Se chegou aqui, precisa de solicitacao_id ou manutencao_id
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Informe solicitacao_id ou manutencao_id"
    )
