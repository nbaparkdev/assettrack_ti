
# app/web/endpoints/maintenance_requests.py
from typing import Annotated
from fastapi import APIRouter, Request, Depends, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from starlette import status

from app.database import get_db
from app.crud.maintenance_request import maintenance_request
from app.schemas.maintenance_request import SolicitacaoManutencaoCreate
from app.schemas.maintenance_request import SolicitacaoManutencaoCreate
from app.models.maintenance_request import SolicitacaoManutencao, PrioridadeSolicitacao, StatusSolicitacaoManutencao
from app.models.transaction import Solicitacao, StatusSolicitacao, Movimentacao
from app.models.maintenance import Manutencao
from app.models.asset import Asset, AssetStatus
from app.models.user import User, UserRole
from app.web.dependencies import get_active_user_web
from app.services.notification_service import notification_service

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


# ===== Páginas para USUÁRIO COMUM =====

@router.get("/solicitar-manutencao", response_class=HTMLResponse)
async def form_nova_solicitacao(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_active_user_web)]
):
    """Formulário para criar nova solicitação de manutenção"""
    # Buscar ativos do usuário (ou todos se for admin/gerente)
    if current_user.role in [UserRole.ADMIN, UserRole.GERENTE]:
        result = await db.execute(
            select(Asset)
            .filter(Asset.status != AssetStatus.BAIXADO)
            .order_by(Asset.nome)
        )
    else:
        # Usuário comum: apenas ativos associados a ele
        result = await db.execute(
            select(Asset)
            .filter(
                Asset.current_user_id == current_user.id,
                Asset.status != AssetStatus.BAIXADO,
                Asset.status != AssetStatus.MANUTENCAO
            )
            .order_by(Asset.nome)
        )
    
    assets = result.scalars().all()
    
    return templates.TemplateResponse("maintenance_requests/form.html", {
        "request": request,
        "user": current_user,
        "title": "Solicitar Manutenção",
        "assets": assets,
        "prioridades": PrioridadeSolicitacao
    })


@router.post("/solicitar-manutencao", response_class=HTMLResponse)
async def submit_nova_solicitacao(
    request: Request,
    asset_id: Annotated[int, Form()],
    descricao: Annotated[str, Form()],
    prioridade: Annotated[str, Form()],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_active_user_web)]
):
    """Processa nova solicitação de manutenção"""
    try:
        obj_in = SolicitacaoManutencaoCreate(
            asset_id=asset_id,
            descricao=descricao,
            prioridade=PrioridadeSolicitacao(prioridade)
        )
        
        new_request = await maintenance_request.create_request(
            db, 
            obj_in=obj_in, 
            solicitante_id=current_user.id
        )
        
        # Buscar asset para notificação
        asset_result = await db.execute(select(Asset).filter(Asset.id == asset_id))
        asset = asset_result.scalar_one_or_none()
        
        # Notificar técnicos, gerentes e admins
        await notification_service.notify_new_maintenance_request(
            db=db,
            request_id=new_request.id,
            asset_name=asset.nome if asset else "Equipamento",
            requester_name=current_user.nome,
            priority=prioridade,
            description=descricao
        )
        
        return RedirectResponse(
            url="/minhas-solicitacoes-manutencao?success=created",
            status_code=status.HTTP_302_FOUND
        )
    except Exception as e:
        # Re-render form with error
        if current_user.role in [UserRole.ADMIN, UserRole.GERENTE]:
            result = await db.execute(select(Asset).filter(Asset.status != AssetStatus.BAIXADO))
        else:
            result = await db.execute(
                select(Asset).filter(
                    Asset.current_user_id == current_user.id,
                    Asset.status != AssetStatus.BAIXADO
                )
            )
        assets = result.scalars().all()
        
        return templates.TemplateResponse("maintenance_requests/form.html", {
            "request": request,
            "user": current_user,
            "title": "Solicitar Manutenção",
            "assets": assets,
            "prioridades": PrioridadeSolicitacao,
            "error": str(e)
        })


@router.get("/minhas-solicitacoes-manutencao", response_class=HTMLResponse)
async def minhas_solicitacoes(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_active_user_web)]
):
    """Lista de solicitações do usuário logado"""
    solicitacoes = await maintenance_request.list_by_user(
        db, 
        user_id=current_user.id
    )
    
    success_msg = None
    if request.query_params.get("success") == "created":
        success_msg = "Solicitação enviada com sucesso!"
    
    return templates.TemplateResponse("maintenance_requests/list_user.html", {
        "request": request,
        "user": current_user,
        "title": "Minhas Solicitações de Manutenção",
        "solicitacoes": solicitacoes,
        "success": success_msg
    })


# ===== Páginas para TÉCNICO/GERENTE/ADMIN =====

@router.get("/solicitacoes-manutencao", response_class=HTMLResponse)
async def painel_solicitacoes(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_active_user_web)]
):
    """Painel de solicitações para técnicos/gerentes"""
    if current_user.role not in [UserRole.ADMIN, UserRole.GERENTE, UserRole.TECNICO]:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    # Filtrar por status
    status_filter = request.query_params.get("status", "pendente")
    
    if status_filter == "all":
        solicitacoes = await maintenance_request.list_all(db)
    else:
        solicitacoes = await maintenance_request.list_pending(db)
    
    success_msg = None
    if request.query_params.get("success") == "accepted":
        success_msg = "Solicitação aceita! Manutenção iniciada."
    elif request.query_params.get("success") == "rejected":
        success_msg = "Solicitação rejeitada."
    
    return templates.TemplateResponse("maintenance_requests/list_tech.html", {
        "request": request,
        "user": current_user,
        "title": "Painel de Solicitações de Manutenção",
        "solicitacoes": solicitacoes,
        "status_filter": status_filter,
        "success": success_msg
    })


@router.get("/solicitacoes-manutencao/{id}", response_class=HTMLResponse)
async def detalhe_solicitacao(
    request: Request,
    id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_active_user_web)]
):
    """Detalhes de uma solicitação"""
    solicitacao = await maintenance_request.get_with_relations(db, id=id)
    
    if not solicitacao:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada")
    
    # Verificar permissão: dono ou técnico/admin
    is_owner = solicitacao.solicitante_id == current_user.id
    is_tech = current_user.role in [UserRole.ADMIN, UserRole.GERENTE, UserRole.TECNICO]
    
    if not is_owner and not is_tech:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    return templates.TemplateResponse("maintenance_requests/detail.html", {
        "request": request,
        "user": current_user,
        "title": f"Solicitação #{id}",
        "solicitacao": solicitacao,
        "is_tech": is_tech,
        "can_respond": is_tech and solicitacao.status == StatusSolicitacaoManutencao.PENDENTE
    })


@router.post("/solicitacoes-manutencao/{id}/aceitar", response_class=HTMLResponse)
async def aceitar_solicitacao(
    request: Request,
    id: int,
    observacao: Annotated[str, Form()] = "",
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    current_user: Annotated[User, Depends(get_active_user_web)] = None
):
    """Aceita uma solicitação e inicia manutenção"""
    if current_user.role not in [UserRole.ADMIN, UserRole.GERENTE, UserRole.TECNICO]:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    # Buscar solicitação com relações para notificação
    solicitacao = await maintenance_request.get_with_relations(db, id=id)
    if not solicitacao:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada")
    
    result = await maintenance_request.accept_request(
        db,
        request_id=id,
        responsavel_id=current_user.id,
        observacao=observacao if observacao else None
    )
    
    if not result:
        raise HTTPException(status_code=400, detail="Não foi possível aceitar esta solicitação")
    
    # Notificar o solicitante
    await notification_service.notify_request_accepted(
        db=db,
        request_id=id,
        requester_email=solicitacao.solicitante.email,
        asset_name=solicitacao.asset.nome,
        technician_name=current_user.nome,
        observation=observacao if observacao else None
    )
    
    return RedirectResponse(
        url="/solicitacoes-manutencao?success=accepted",
        status_code=status.HTTP_302_FOUND
    )


@router.post("/solicitacoes-manutencao/{id}/rejeitar", response_class=HTMLResponse)
async def rejeitar_solicitacao(
    request: Request,
    id: int,
    observacao: Annotated[str, Form()],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_active_user_web)]
):
    """Rejeita uma solicitação"""
    if current_user.role not in [UserRole.ADMIN, UserRole.GERENTE, UserRole.TECNICO]:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    if not observacao or len(observacao) < 10:
        raise HTTPException(status_code=400, detail="Justificativa obrigatória (mínimo 10 caracteres)")
    
    # Buscar solicitação com relações para notificação
    solicitacao = await maintenance_request.get_with_relations(db, id=id)
    if not solicitacao:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada")
    
    result = await maintenance_request.reject_request(
        db,
        request_id=id,
        responsavel_id=current_user.id,
        observacao=observacao
    )
    
    if not result:
        raise HTTPException(status_code=400, detail="Não foi possível rejeitar esta solicitação")
    
    # Notificar o solicitante
    await notification_service.notify_request_rejected(
        db=db,
        request_id=id,
        requester_email=solicitacao.solicitante.email,
        asset_name=solicitacao.asset.nome,
        technician_name=current_user.nome,
        reason=observacao
    )
    
    return RedirectResponse(
        url="/solicitacoes-manutencao?success=rejected",
        status_code=status.HTTP_302_FOUND
    )


# ===== CONCLUSÃO E ENTREGA =====

@router.post("/solicitacoes-manutencao/{id}/concluir", response_class=HTMLResponse)
async def concluir_manutencao(
    request: Request,
    id: int,
    observacao: Annotated[str, Form()] = "",
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    current_user: Annotated[User, Depends(get_active_user_web)] = None
):
    """Técnico marca manutenção como concluída (aguardando entrega)"""
    if current_user.role not in [UserRole.ADMIN, UserRole.GERENTE, UserRole.TECNICO]:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    # Buscar solicitação para notificação
    solicitacao = await maintenance_request.get_with_relations(db, id=id)
    if not solicitacao:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada")
    
    result = await maintenance_request.complete_maintenance(
        db,
        request_id=id,
        observacao_conclusao=observacao if observacao else None
    )
    
    if not result:
        raise HTTPException(status_code=400, detail="Não foi possível concluir. Verifique se está em andamento.")
    
    # Notificar o solicitante que pode retirar o equipamento
    await notification_service.notify_request_accepted(
        db=db,
        request_id=id,
        requester_email=solicitacao.solicitante.email,
        asset_name=solicitacao.asset.nome,
        technician_name=current_user.nome,
        observation=f"Manutenção concluída! {observacao if observacao else 'Seu equipamento está pronto para retirada.'}"
    )
    
    return RedirectResponse(
        url="/solicitacoes-manutencao?success=completed",
        status_code=status.HTTP_302_FOUND
    )


@router.get("/aguardando-entrega", response_class=HTMLResponse)
async def lista_aguardando_entrega(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_active_user_web)]
):
    """Lista equipamentos prontos para o usuário confirmar recebimento"""
    solicitacoes = await maintenance_request.list_awaiting_delivery(
        db, 
        user_id=current_user.id
    )
    
    success_msg = None
    if request.query_params.get("success") == "confirmed":
        success_msg = "Recebimento confirmado com sucesso!"
    
    return templates.TemplateResponse("maintenance_requests/awaiting_delivery.html", {
        "request": request,
        "user": current_user,
        "title": "Equipamentos Prontos para Retirada",
        "solicitacoes": solicitacoes,
        "success": success_msg
    })


@router.get("/solicitacoes-manutencao/{id}/confirmar-entrega", response_class=HTMLResponse)
async def confirmar_entrega_page(
    request: Request,
    id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_active_user_web)]
):
    """Página para técnico confirmar entrega escaneando QR do usuário"""
    if current_user.role not in [UserRole.ADMIN, UserRole.GERENTE, UserRole.TECNICO]:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    solicitacao = await maintenance_request.get_with_relations(db, id=id)
    if not solicitacao:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada")
    
    if solicitacao.status != StatusSolicitacaoManutencao.AGUARDANDO_ENTREGA:
        raise HTTPException(status_code=400, detail="Esta solicitação não está aguardando entrega")
    
    return templates.TemplateResponse("maintenance_requests/confirmar_entrega.html", {
        "request": request,
        "user": current_user,
        "solicitacao": solicitacao,
        "title": f"Confirmar Entrega - #{id}"
    })


@router.post("/solicitacoes-manutencao/{id}/confirmar-entrega", response_class=HTMLResponse)
async def confirmar_entrega_submit(
    request: Request,
    id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_active_user_web)],
    qr_token: Annotated[str, Form()] = "",
    observacao: Annotated[str, Form()] = ""
):
    """Processa confirmação de entrega - valida QR do usuário"""
    from app.crud import user as user_crud
    
    if current_user.role not in [UserRole.ADMIN, UserRole.GERENTE, UserRole.TECNICO]:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    solicitacao = await maintenance_request.get_with_relations(db, id=id)
    if not solicitacao:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada")
    
    if solicitacao.status != StatusSolicitacaoManutencao.AGUARDANDO_ENTREGA:
        raise HTTPException(status_code=400, detail="Esta solicitação não está aguardando entrega")
    
    # Validar QR Code do usuário
    if not qr_token or not qr_token.strip():
        return templates.TemplateResponse("maintenance_requests/confirmar_entrega.html", {
            "request": request,
            "user": current_user,
            "solicitacao": solicitacao,
            "error": "Escaneie o QR Code do usuário para confirmar a entrega!",
            "title": f"Confirmar Entrega - #{id}"
        })
    
    qr_user = await user_crud.user.get_by_qr_token(db, token=qr_token.strip())
    if not qr_user:
        return templates.TemplateResponse("maintenance_requests/confirmar_entrega.html", {
             "request": request,
             "user": current_user,
             "solicitacao": solicitacao,
             "error": "QR Code inválido! Nenhum usuário encontrado.",
             "title": f"Confirmar Entrega - #{id}"
        })
        
    if qr_user.id != solicitacao.solicitante_id:
        return templates.TemplateResponse("maintenance_requests/confirmar_entrega.html", {
            "request": request,
            "user": current_user,
            "solicitacao": solicitacao,
            "error": "QR Code inválido ou não pertence ao solicitante da manutenção!",
            "title": f"Confirmar Entrega - #{id}"
        })
    
    # QR válido - confirmar entrega
    result = await maintenance_request.confirm_delivery_by_tech(
        db,
        request_id=id,
        tech_id=current_user.id,
        observation=observacao if observacao else None
    )
    
    if not result:
        raise HTTPException(status_code=400, detail="Erro ao confirmar entrega")

    # Notificar Gerentes/Admins sobre a entrega
    await notification_service.notify_delivery_completed(
        db=db,
        request_id=id,
        asset_name=result.asset.nome,
        requester_name=result.solicitante.nome,
        technician_name=current_user.nome,
        observation=observacao
    )
    
    return RedirectResponse(
        url="/solicitacoes-manutencao?success=delivered",
        status_code=status.HTTP_302_FOUND
    )


@router.post("/solicitacoes-manutencao/{id}/confirmar-recebimento", response_class=HTMLResponse)
async def confirmar_recebimento_submit(
    request: Request,
    id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_active_user_web)]
):
    """Usuário confirma que recebeu o equipamento"""
    
    solicitacao = await maintenance_request.get_with_relations(db, id=id)
    if not solicitacao:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada")
    
    # Apenas o solicitante pode confirmar
    if solicitacao.solicitante_id != current_user.id:
        raise HTTPException(status_code=403, detail="Apenas o solicitante pode confirmar o recebimento")
    
    if solicitacao.status != StatusSolicitacaoManutencao.ENTREGUE:
        raise HTTPException(status_code=400, detail="Esta solicitação não está aguardando confirmação de recebimento")
    
    result = await maintenance_request.confirm_receipt_by_user(
        db,
        request_id=id,
        user_id=current_user.id
    )
    
    if not result:
        raise HTTPException(status_code=400, detail="Erro ao confirmar recebimento")
    
    return RedirectResponse(
        url="/minhas-solicitacoes-manutencao?success=completed",
        status_code=status.HTTP_302_FOUND
    )


# ===== Scanner de QR de Usuário =====

@router.get("/manutencao/entrega/scanner", response_class=HTMLResponse)
async def usuario_scanner_page(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_active_user_web)]
):
    """Página para técnico escanear QR de usuário e ver entregas pendentes"""
    if current_user.role not in [UserRole.ADMIN, UserRole.GERENTE, UserRole.TECNICO]:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    return templates.TemplateResponse("maintenance_requests/usuario_scanner.html", {
        "request": request,
        "user": current_user,
        "title": "Validar Entrega - Escanear QR do Usuário"
    })


@router.post("/manutencao/entrega/scanner", response_class=HTMLResponse)
async def usuario_scanner_submit(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_active_user_web)],
    qr_token: Annotated[str, Form()] = ""
):
    """Busca usuário pelo QR e mostra entregas pendentes"""
    from app.crud import user as user_crud
    
    if current_user.role not in [UserRole.ADMIN, UserRole.GERENTE, UserRole.TECNICO]:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    if not qr_token or not qr_token.strip():
        return templates.TemplateResponse("maintenance_requests/usuario_scanner.html", {
            "request": request,
            "user": current_user,
            "title": "Validar Entrega - Escanear QR do Usuário",
            "error": "Por favor, escaneie ou insira o QR Code do usuário"
        })
    
    # Buscar usuário pelo QR Token
    qr_user = await user_crud.user.get_by_qr_token(db, token=qr_token.strip())
    if not qr_user:
        return templates.TemplateResponse("maintenance_requests/usuario_scanner.html", {
            "request": request,
            "user": current_user,
            "title": "Validar Entrega - Escanear QR do Usuário",
            "error": "QR Code inválido! Nenhum usuário encontrado."
        })
    
    # Buscar solicitações DE MANUTENÇÃO AGUARDANDO_ENTREGA deste usuário
    awaiting_maintenance = await maintenance_request.list_by_user_and_status(
        db, 
        user_id=qr_user.id, 
        status=StatusSolicitacaoManutencao.AGUARDANDO_ENTREGA
    )
    
    # Buscar solicitações DE ATIVOS APROVADAS (Pendente de Entrega)
    result_sol = await db.execute(
        select(Solicitacao)
        .options(selectinload(Solicitacao.asset), selectinload(Solicitacao.solicitante))
        .filter(
            Solicitacao.solicitante_id == qr_user.id,
            Solicitacao.status == StatusSolicitacao.APROVADA
        )
        .order_by(Solicitacao.data_solicitacao.desc())
    )
    awaiting_assets = result_sol.scalars().all()

    # === BUSCAR HISTÓRICO COMPLETO (SOLICITAÇÃO DO USUÁRIO) ===
    
    # 1. Histórico de Solicitações (Geral - incluindo concluídas)
    hist_sol_result = await db.execute(
        select(Solicitacao)
        .options(selectinload(Solicitacao.asset))
        .filter(Solicitacao.solicitante_id == qr_user.id)
        .order_by(Solicitacao.data_solicitacao.desc())
        .limit(10)
    )
    history_solicitacoes = hist_sol_result.scalars().all()
    
    # 2. Histórico de Movimentações
    hist_mov_result = await db.execute(
        select(Movimentacao)
        .filter(
            (Movimentacao.de_user_id == qr_user.id) | 
            (Movimentacao.para_user_id == qr_user.id)
        )
        .order_by(Movimentacao.data.desc())
        .limit(10)
    )
    history_movimentacoes = hist_mov_result.scalars().all()
    
    # 3. Histórico de Manutenções (Geral)
    # Nota: Manutencao vs SolicitacaoManutencao -> O sistema parece usar SolicitacaoManutencao para o fluxo
    # Mas o user_public_profile usava Manutencao. Vamos verificar qual é o correto.
    # O user_public_profile.py usa: from app.models.maintenance import Manutencao
    # O maintenance_requests.py usa: SolicitacaoManutencao.
    # Se Manutencao for a tabela antiga ou de registro, devemos usar SolicitacaoManutencao que é o que está sendo usado no fluxo atual.
    # Vamos puxar SolicitacaoManutencao para o histórico também.
    
    hist_man_result = await db.execute(
        select(SolicitacaoManutencao)
        .options(selectinload(SolicitacaoManutencao.asset))
        .filter(SolicitacaoManutencao.solicitante_id == qr_user.id)
        .order_by(SolicitacaoManutencao.data_solicitacao.desc())
        .limit(10)
    )
    history_manutencoes = hist_man_result.scalars().all()
    
    # Combinar as listas para exibição (pode precisar ajustar o template para lidar com tipos diferentes ou normalizar)
    # Por enquanto, vamos passar ambas as listas e o template que lide com isso
    
    return templates.TemplateResponse("maintenance_requests/usuario_scanner_result.html", {
        "request": request,
        "user": current_user,
        "target_user": qr_user,
        "solicitacoes_manutencao": awaiting_maintenance,
        "solicitacoes_ativos": awaiting_assets,
        
        # Histórico
        "history_solicitacoes": history_solicitacoes,
        "history_movimentacoes": history_movimentacoes,
        "history_manutencoes": history_manutencoes,
        
        "title": f"Entregas Pendentes - {qr_user.nome}"
    })


# ===== Relatórios =====

@router.get("/solicitacoes-manutencao/administrativo/relatorios", response_class=HTMLResponse)
async def relatorio_manutencao(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_active_user_web)],
    start_date: str = "",
    end_date: str = "",
    status_filter: str = "",
    tech_id: int = 0
):
    """Página de relatórios de manutenção"""
    if current_user.role not in [UserRole.ADMIN, UserRole.GERENTE, UserRole.TECNICO]:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    # Importar User crud para listar técnicos no filtro
    from app.crud import user as user_crud
    from datetime import datetime
    
    # Processar filtros
    dt_start = None
    dt_end = None
    
    if start_date:
        try:
            dt_start = datetime.strptime(start_date, "%Y-%m-%d")
        except:
            pass
            
    if end_date:
        try:
            dt_end = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
        except:
            pass
            
    status_enum = None
    if status_filter:
        try:
            status_enum = StatusSolicitacaoManutencao(status_filter)
        except:
            pass
            
    # Buscar dados
    results = await maintenance_request.get_reports(
        db,
        start_date=dt_start,
        end_date=dt_end,
        status=status_enum,
        responsavel_id=tech_id if tech_id > 0 else None
    )
    
    # Buscar técnicos para o filtro
    # Assumindo que temos um método list_by_role ou similar. Se não, list all e filtra.
    # Por simplicidade, vamos pegar todos usuarios que tem role tecnico/admin/gerente
    tecnicos_result = await db.execute(
        select(User).filter(User.role.in_([UserRole.TECNICO, UserRole.ADMIN, UserRole.GERENTE]))
    )
    tecnicos = tecnicos_result.scalars().all()

    return templates.TemplateResponse("maintenance_requests/reports.html", {
        "request": request,
        "user": current_user,
        "title": "Relatórios de Manutenção",
        "solicitacoes": results,
        "tecnicos": tecnicos,
        "filters": {
            "start_date": start_date,
            "end_date": end_date,
            "status": status_filter,
            "tech_id": tech_id
        },
        "statuses": StatusSolicitacaoManutencao
    })
