
# app/web/endpoints/assets.py
from typing import Annotated, Optional
from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, datetime

from app.web.dependencies import get_active_user_web
from app.models.user import User, UserRole
from app.models.asset import AssetStatus
from app.schemas.asset import AssetCreate, AssetUpdate
from app.models.transaction import Movimentacao, TipoMovimentacao, Solicitacao, StatusSolicitacao
from app.database import get_db
from app.crud import transaction as transaction_crud
from app.crud import asset as asset_crud
from app.services.qr_service import QRService

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def list_assets(
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    assets = await asset_crud.asset.get_multi(db)
    return templates.TemplateResponse("assets/list.html", {
        "request": request,
        "user": current_user,
        "assets": assets,
        "title": "Ativos"
    })

@router.get("/scanner", response_class=HTMLResponse)
async def scanner_page(
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)]
):
    """QR Code scanner page for mobile devices"""
    return templates.TemplateResponse("scanner.html", {
        "request": request,
        "user": current_user,
        "title": "Scanner QR Code"
    })

@router.get("/search", response_class=HTMLResponse)
async def search_asset(
    request: Request,
    serial: str,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Search asset by serial number and redirect to detail page"""
    from sqlalchemy import select
    from app.models.asset import Asset
    
    result = await db.execute(
        select(Asset).where(Asset.serial_number.ilike(f"%{serial}%"))
    )
    asset = result.scalar_one_or_none()
    
    if asset:
        return RedirectResponse(url=f"/assets/{asset.id}", status_code=303)
    
    # If not found, redirect to list with error message
    return RedirectResponse(url="/assets/?error=not_found", status_code=303)

@router.get("/new", response_class=HTMLResponse)
async def new_asset_form(
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)]
):
    return templates.TemplateResponse("assets/form.html", {
        "request": request,
        "user": current_user,
        "title": "Novo Ativo"
    })

@router.post("/new", response_class=HTMLResponse)
async def create_asset(
    request: Request,
    nome: Annotated[str, Form()],
    modelo: Annotated[str, Form()],
    serial_number: Annotated[str, Form()],
    descricao: Annotated[Optional[str], Form()] = None,
    data_aquisicao: Annotated[Optional[str], Form()] = None, # Changed to str to handle empty form input
    valor_aquisicao: Annotated[Optional[str], Form()] = None, # Changed to str to handle empty form input
    current_user: Annotated[User, Depends(get_active_user_web)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
):
    try:
        # Handle empty strings from form
        dt_aquisicao = None
        if data_aquisicao:
            dt_aquisicao = datetime.strptime(data_aquisicao, "%Y-%m-%d").date()
        
        val_aquisicao = None
        if valor_aquisicao:
            try:
                # Handle Brazilian currency format (1.200,50 -> 1200.50)
                clean_value = valor_aquisicao.replace('.', '').replace(',', '.') if ',' in valor_aquisicao and '.' in valor_aquisicao else valor_aquisicao.replace(',', '.')
                val_aquisicao = float(clean_value)
            except ValueError:
                # If conversion fails but user provided input, raise error to notify user
                raise ValueError(f"Valor inválido: {valor_aquisicao}")

        asset_in = AssetCreate(
            nome=nome,
            modelo=modelo,
            serial_number=serial_number,
            descricao=descricao,
            data_aquisicao=dt_aquisicao,
            valor=val_aquisicao,
            status=AssetStatus.DISPONIVEL
        )
        await asset_crud.asset.create(db, obj_in=asset_in)
        return RedirectResponse(url="/assets", status_code=303)
    except Exception as e:
        return templates.TemplateResponse("assets/form.html", {
            "request": request,
            "user": current_user,
            "error": f"Erro ao criar ativo: {str(e)}",
            "title": "Novo Ativo"
        })

@router.get("/qrcode/{asset_id}")
async def get_asset_qrcode_web(
    asset_id: int,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Gera QR Code para o ativo (autenticação via cookie)"""
    asset = await asset_crud.asset.get(db, id=asset_id)
    if not asset:
        return Response(content=b"", status_code=404)
    
    # URL completa para acessar o ativo
    qr_content = f"http://localhost:8000/assets/{asset.id}"
    img_io = QRService.generate_qr_code(qr_content)
    
    return Response(content=img_io.getvalue(), media_type="image/png")

@router.get("/{asset_id}", response_class=HTMLResponse)
async def asset_detail(
    request: Request,
    asset_id: int,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    asset = await asset_crud.asset.get(db, id=asset_id)
    if not asset:
         return templates.TemplateResponse("assets/list.html", {
            "request": request,
            "user": current_user,
            "error": "Ativo não encontrado.",
             "assets": [],
            "title": "Ativos"
        })
        
    return templates.TemplateResponse("assets/detail.html", {
        "request": request,
        "user": current_user,
        "asset": asset,
        "title": f"Ativo: {asset.nome}"
    })

@router.get("/{asset_id}/edit", response_class=HTMLResponse)
async def edit_asset_form(
    request: Request,
    asset_id: int,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    if current_user.role not in [UserRole.ADMIN, UserRole.GERENTE]:
         # Only managers can edit assets
        return RedirectResponse(url=f"/assets/{asset_id}", status_code=303)

    asset = await asset_crud.asset.get(db, id=asset_id)
    if not asset:
        return RedirectResponse(url="/assets", status_code=303)

    return templates.TemplateResponse("assets/form.html", {
        "request": request,
        "user": current_user,
        "asset": asset,
        "title": f"Editar Ativo: {asset.nome}"
    })

@router.post("/{asset_id}/edit", response_class=HTMLResponse)
async def update_asset(
    request: Request,
    asset_id: int,
    nome: Annotated[str, Form()],
    modelo: Annotated[str, Form()],
    serial_number: Annotated[str, Form()],
    descricao: Annotated[Optional[str], Form()] = None,
    data_aquisicao: Annotated[Optional[str], Form()] = None,
    valor_aquisicao: Annotated[Optional[str], Form()] = None,
    current_user: Annotated[User, Depends(get_active_user_web)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
):
    if current_user.role not in [UserRole.ADMIN, UserRole.GERENTE]:
        return RedirectResponse(url=f"/assets/{asset_id}", status_code=303)

    asset = await asset_crud.asset.get(db, id=asset_id)
    if not asset:
         return RedirectResponse(url="/assets", status_code=303)

    try:
        # Handle empty strings from form
        dt_aquisicao = None
        if data_aquisicao:
            dt_aquisicao = datetime.strptime(data_aquisicao, "%Y-%m-%d").date()
        
        val_aquisicao = None
        if valor_aquisicao:
            try:
                # Handle Brazilian currency format (1.200,50 -> 1200.50)
                clean_value = valor_aquisicao.replace('.', '').replace(',', '.') if ',' in valor_aquisicao and '.' in valor_aquisicao else valor_aquisicao.replace(',', '.')
                val_aquisicao = float(clean_value)
            except ValueError:
                raise ValueError(f"Valor inválido: {valor_aquisicao}")

        asset_update = AssetUpdate(
            nome=nome,
            modelo=modelo,
            serial_number=serial_number,
            descricao=descricao if descricao else None,
            data_aquisicao=dt_aquisicao,
            valor=val_aquisicao
        )
        await asset_crud.asset.update(db, db_obj=asset, obj_in=asset_update)
        return RedirectResponse(url=f"/assets/{asset_id}", status_code=303)
    except Exception as e:
        return templates.TemplateResponse("assets/form.html", {
            "request": request,
            "user": current_user,
            "asset": asset,
            "error": f"Erro ao atualizar ativo: {str(e)}",
            "title": f"Editar Ativo: {asset.nome}"
        })

@router.post("/{asset_id}/delete", response_class=HTMLResponse)
async def delete_asset(
    request: Request,
    asset_id: int,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    if current_user.role not in [UserRole.ADMIN, UserRole.GERENTE]:
        return RedirectResponse(url=f"/assets/{asset_id}", status_code=303)
    
    asset = await asset_crud.asset.get(db, id=asset_id)
    if not asset:
        return RedirectResponse(url="/assets", status_code=303)
    
    try:
        await asset_crud.asset.remove(db, id=asset_id)
        return RedirectResponse(url="/assets", status_code=303)
    except Exception as e:
        await db.rollback()
        
        # Explicitly eager load relationships to prevent MissingGreenlet in template
        from sqlalchemy.orm import selectinload
        from sqlalchemy import select
        
        # Re-fetch asset with necessary relationships
        result = await db.execute(
            select(Asset)
            .options(
                selectinload(Asset.current_user),
                selectinload(Asset.current_armazenamento),
                selectinload(Asset.current_local)
            )
            .filter(Asset.id == asset_id)
        )
        asset = result.scalars().first()
        
        error_msg = f"Erro ao excluir ativo: {str(e)}"
        if "constraint" in str(e).lower() or "cforeign" in str(e).lower():
             error_msg = "Não é possível excluir este ativo pois ele possui histórico (movimentações, solicitações, etc). Considere apenas atualizar o status para 'Baixado'."

        return templates.TemplateResponse("assets/detail.html", {
            "request": request,
            "user": current_user,
            "asset": asset,
            "error": error_msg,
            "title": f"Ativo: {asset.nome}"
        })

@router.post("/{asset_id}/return", response_class=HTMLResponse)
async def return_asset(
    request: Request,
    asset_id: int,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    if current_user.role not in [UserRole.ADMIN, UserRole.GERENTE, UserRole.TECNICO]:
        return RedirectResponse(url=f"/assets/{asset_id}", status_code=303)
    
    asset = await asset_crud.asset.get(db, id=asset_id)
    if not asset or asset.status != AssetStatus.EM_USO:
        return RedirectResponse(url=f"/assets/{asset_id}", status_code=303)
    
    previous_user_id = asset.current_user_id
    
    # 1. Update Asset
    asset.status = AssetStatus.DISPONIVEL
    asset.current_user_id = None
    db.add(asset)
    
    # 2. Register Movement (Devolucao)
    movimentacao = Movimentacao(
        asset_id=asset.id,
        tipo=TipoMovimentacao.DEVOLUCAO,
        de_user_id=previous_user_id, # User who is returning
        para_user_id=current_user.id, # Manager who received
        data=datetime.now(),
        observacao=f"Devolução registrada por {current_user.nome}"
    )
    db.add(movimentacao)
    
    await db.commit()
    return RedirectResponse(url=f"/assets/{asset_id}", status_code=303)

@router.get("/{asset_id}/maintenance/start", response_class=HTMLResponse)
async def start_maintenance_form(
    request: Request,
    asset_id: int,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    if current_user.role not in [UserRole.ADMIN, UserRole.GERENTE, UserRole.TECNICO]:
        return RedirectResponse(url=f"/assets/{asset_id}", status_code=303)
    
    asset = await asset_crud.asset.get(db, id=asset_id)
    if not asset or asset.status not in [AssetStatus.DISPONIVEL, AssetStatus.EM_USO]:
        return RedirectResponse(url=f"/assets/{asset_id}", status_code=303)
    
    return templates.TemplateResponse("maintenance/form.html", {
        "request": request,
        "user": current_user,
        "asset": asset,
        "title": f"Manutenção: {asset.nome}"
    })

@router.post("/{asset_id}/maintenance/start", response_class=HTMLResponse)
async def start_maintenance(
    request: Request,
    asset_id: int,
    motivo: Annotated[str, Form()],
    tipo: Annotated[str, Form()],
    data_previsao: Annotated[Optional[str], Form()] = None,
    current_user: Annotated[User, Depends(get_active_user_web)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
):
    from app.models.maintenance import Manutencao, TipoManutencao, StatusManutencao
    
    if current_user.role not in [UserRole.ADMIN, UserRole.GERENTE, UserRole.TECNICO]:
        return RedirectResponse(url=f"/assets/{asset_id}", status_code=303)
    
    asset = await asset_crud.asset.get(db, id=asset_id)
    if not asset or asset.status not in [AssetStatus.DISPONIVEL, AssetStatus.EM_USO]:
        return RedirectResponse(url=f"/assets/{asset_id}", status_code=303)
    
    previous_user_id = asset.current_user_id
    
    # Parse date if provided
    dt_previsao = None
    if data_previsao:
        try:
            dt_previsao = datetime.strptime(data_previsao, "%Y-%m-%d")
        except ValueError:
            pass

    # 1. Create Manutencao record
    manutencao = Manutencao(
        asset_id=asset.id,
        responsavel_id=current_user.id,
        motivo=motivo,
        tipo=TipoManutencao(tipo),
        data_entrada=datetime.now(),
        data_previsao=dt_previsao,
        status=StatusManutencao.EM_ANDAMENTO
    )
    db.add(manutencao)
    
    # 2. Update Asset
    asset.status = AssetStatus.MANUTENCAO
    asset.current_user_id = None
    db.add(asset)
    
    # 3. Register Movement
    movimentacao = Movimentacao(
        asset_id=asset.id,
        tipo=TipoMovimentacao.MANUTENCAO,
        de_user_id=previous_user_id,
        para_user_id=current_user.id,
        data=datetime.now(),
        observacao=f"Enviado para manutenção ({tipo}): {motivo[:100]}"
    )
    db.add(movimentacao)
    
    await db.commit()
    return RedirectResponse(url=f"/assets/{asset_id}", status_code=303)

@router.get("/{asset_id}/maintenance/finish", response_class=HTMLResponse)
async def finish_maintenance_form(
    request: Request,
    asset_id: int,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from app.models.maintenance import Manutencao, StatusManutencao
    
    if current_user.role not in [UserRole.ADMIN, UserRole.GERENTE, UserRole.TECNICO]:
        return RedirectResponse(url=f"/assets/{asset_id}", status_code=303)
    
    asset = await asset_crud.asset.get(db, id=asset_id)
    if not asset or asset.status != AssetStatus.MANUTENCAO:
        return RedirectResponse(url=f"/assets/{asset_id}", status_code=303)
    
    # Get current maintenance record
    result = await db.execute(
        select(Manutencao)
        .filter(Manutencao.asset_id == asset_id, Manutencao.status == StatusManutencao.EM_ANDAMENTO)
        .order_by(Manutencao.data_entrada.desc())
    )
    manutencao = result.scalars().first()
    
    # Get active users for destination selection
    from app.models.user import User
    result = await db.execute(
        select(User).filter(User.is_active == True).order_by(User.nome)
    )
    users = result.scalars().all()
    
    # Get pending solicitations for this asset
    result = await db.execute(
        select(Solicitacao)
        .options(selectinload(Solicitacao.solicitante))
        .filter(Solicitacao.asset_id == asset_id, Solicitacao.status == StatusSolicitacao.PENDENTE)
        .order_by(Solicitacao.data_solicitacao.asc())
    )
    pending_solicitations = result.scalars().all()
    
    return templates.TemplateResponse("maintenance/finish_form.html", {
        "request": request,
        "user": current_user,
        "asset": asset,
        "manutencao": manutencao,
        "users": users,
        "pending_solicitations": pending_solicitations,
        "title": f"Concluir Manutenção: {asset.nome}"
    })

@router.post("/{asset_id}/maintenance/finish", response_class=HTMLResponse)
async def finish_maintenance(
    request: Request,
    asset_id: int,
    observacao_conclusao: Annotated[str, Form()],
    destino_tipo: Annotated[str, Form()],
    custo: Annotated[Optional[str], Form()] = None,
    destino_user_id: Annotated[Optional[str], Form()] = None,
    current_user: Annotated[User, Depends(get_active_user_web)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
):
    from sqlalchemy import select
    from app.models.maintenance import Manutencao, StatusManutencao, DestinoManutencao
    
    if current_user.role not in [UserRole.ADMIN, UserRole.GERENTE, UserRole.TECNICO]:
        return RedirectResponse(url=f"/assets/{asset_id}", status_code=303)
    
    asset = await asset_crud.asset.get(db, id=asset_id)
    if not asset or asset.status != AssetStatus.MANUTENCAO:
        return RedirectResponse(url=f"/assets/{asset_id}", status_code=303)
    
    # Get current maintenance record
    result = await db.execute(
        select(Manutencao)
        .filter(Manutencao.asset_id == asset_id, Manutencao.status == StatusManutencao.EM_ANDAMENTO)
        .order_by(Manutencao.data_entrada.desc())
    )
    manutencao = result.scalars().first()
    
    # Parse cost if provided
    val_custo = None
    if custo:
        try:
            val_custo = float(custo)
        except ValueError:
            pass
    
    # Parse user id if provided
    user_id = None
    if destino_user_id:
        try:
            user_id = int(destino_user_id)
        except ValueError:
            pass
    
    # 1. Update Manutencao record
    if manutencao:
        manutencao.status = StatusManutencao.CONCLUIDA
        manutencao.data_conclusao = datetime.now()
        manutencao.observacao_conclusao = observacao_conclusao
        manutencao.custo = val_custo
        manutencao.destino_tipo = DestinoManutencao(destino_tipo)
        manutencao.destino_user_id = user_id if destino_tipo == "usuario" else None
        db.add(manutencao)
    
    # 2. Update Asset based on destination
    if destino_tipo == "usuario" and user_id:
        asset.status = AssetStatus.EM_USO
        asset.current_user_id = user_id
        observacao_mov = f"Manutenção concluída e atribuído a usuário: {observacao_conclusao[:80]}"
        
        # Get user name for movement record
        from app.models.user import User
        result = await db.execute(select(User).filter(User.id == user_id))
        destino_user = result.scalars().first()
        para_user_id = user_id
        
        # Register empréstimo movement
        movimento_emprestimo = Movimentacao(
            asset_id=asset.id,
            tipo=TipoMovimentacao.EMPRESTIMO,
            de_user_id=current_user.id,
            para_user_id=para_user_id,
            data=datetime.now(),
            observacao=f"Atribuído após manutenção para {destino_user.nome if destino_user else 'usuário'}"
        )
        db.add(movimento_emprestimo)
    else:
        asset.status = AssetStatus.DISPONIVEL
        asset.current_user_id = None
        observacao_mov = f"Manutenção concluída e disponibilizado: {observacao_conclusao[:80]}"
        para_user_id = None
    
    db.add(asset)
    
    # 3. Register Manutenção return movement
    movimentacao = Movimentacao(
        asset_id=asset.id,
        tipo=TipoMovimentacao.MANUTENCAO,
        de_user_id=current_user.id,
        para_user_id=para_user_id,
        data=datetime.now(),
        observacao=observacao_mov
    )
    db.add(movimentacao)
    
    await db.commit()
    return RedirectResponse(url=f"/assets/{asset_id}", status_code=303)


@router.get("/{asset_id}/transfer", response_class=HTMLResponse)
async def transfer_asset_form(
    request: Request,
    asset_id: int,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    asset = await asset_crud.asset.get(db, id=asset_id)
    if not asset:
        return RedirectResponse(url="/assets", status_code=303)
    
    # Get active users for destination selection
    from sqlalchemy import select
    from app.models.user import User
    result = await db.execute(
        select(User).filter(User.is_active == True).order_by(User.nome)
    )
    users = result.scalars().all()
    
    return templates.TemplateResponse("assets/transfer.html", {
        "request": request,
        "user": current_user,
        "asset": asset,
        "users": users,
        "title": f"Transferir: {asset.nome}"
    })


@router.post("/{asset_id}/transfer", response_class=HTMLResponse)
async def transfer_asset(
    request: Request,
    asset_id: int,
    destinatario_id: Annotated[int, Form()],
    motivo: Annotated[str, Form()],
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    try:
        asset = await asset_crud.asset.get(db, id=asset_id)
        if not asset:
            return RedirectResponse(url="/assets", status_code=303)

        # Create Solicitation (Transferencia)
        solicitacao = Solicitacao(
            solicitante_id=current_user.id, # Quem está pedindo a transferência (pode ser o atual dono ou admin)
            asset_id=asset.id,
            motivo=f"[TRANSFERÊNCIA] Para user ID {destinatario_id}: {motivo}",
            status=StatusSolicitacao.PENDENTE,
            data_solicitacao=datetime.utcnow()
        )
        
        # Override solicitante to be the target user (so the request shows up for them/admin as for them)
        solicitacao.solicitante_id = destinatario_id
        solicitacao.motivo = f"Transferência solicitada por {current_user.nome}: {motivo}"
        
        db.add(solicitacao)
        await db.commit()
        
        return RedirectResponse(url=f"/assets/{asset_id}", status_code=303)
    except Exception as e:
        import traceback
        error_msg = traceback.format_exc()
        return Response(content=f"ERRO DEBUG: {error_msg}", status_code=500, media_type="text/plain")


@router.post("/{asset_id}/baixa", response_class=HTMLResponse)
async def write_off_asset(
    request: Request,
    asset_id: int,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    if current_user.role not in [UserRole.ADMIN, UserRole.GERENTE]:
        return RedirectResponse(url=f"/assets/{asset_id}", status_code=303)
    
    asset = await asset_crud.asset.get(db, id=asset_id)
    if not asset:
        return RedirectResponse(url="/assets", status_code=303)

    previous_user = asset.current_user_id
    
    # Update Asset
    asset.status = AssetStatus.BAIXADO
    asset.current_user_id = None
    db.add(asset)
    
    # Create Movement
    movimentacao = Movimentacao(
        asset_id=asset.id,
        tipo=TipoMovimentacao.BAIXA,
        de_user_id=previous_user,
        para_user_id=None, # Gone
        data=datetime.now(),
        observacao=f"Baixa efetuada por {current_user.nome}"
    )
    db.add(movimentacao)
    
    await db.commit()
    
    return RedirectResponse(url=f"/assets/{asset_id}", status_code=303)

