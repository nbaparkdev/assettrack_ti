# app/web/endpoints/kanban.py
import os
import uuid
from typing import Annotated, List, Optional
from datetime import datetime
from fastapi import APIRouter, Request, Depends, Form, HTTPException, status, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.user import User, UserRole
from app.models.asset import Asset
from app.models.location import Departamento
from app.models.procurement import (
    CostCenter, PurchaseRequest, PurchaseRequestItem, PurchaseProduct,
    MaterialStock, ProductType, PurchaseRequestStatus, PurchaseCategory
)
from app.crud.procurement import generate_request_number, create_or_update_stock
from app.crud.kanban import crud_kanban
from app.crud import user as user_crud
from app.web.dependencies import get_active_user_web, check_kanban_enabled

router = APIRouter(prefix="/kanban", tags=["Kanban Projects"])
templates = Jinja2Templates(directory="app/templates")

# Utility to check project access for common users
def user_can_access_project(user: User, project) -> bool:
    role_str = user.role.value.lower() if hasattr(user.role, 'value') else str(user.role).lower()
    if role_str in ["admin", "gerente_ti", "gerente_infra", "tecnico", "comprador", "rh"]:
        return True
    if project.criador_id == user.id:
        return True
    return any(p.id == user.id for p in project.participantes)

@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
async def list_projects(
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)],
    _: None = Depends(check_kanban_enabled),
    ver_arquivados: bool = False
):
    projects = await crud_kanban.get_user_projects(db, current_user, include_archived=ver_arquivados)
    
    # Calculate stats per project — gradual progress based on column position
    projects_with_stats = []
    for proj in projects:
        total_cards = sum(len(col.cards) for col in proj.colunas)
        num_cols = len(proj.colunas)

        if total_cards > 0 and num_cols > 1:
            weighted_sum = 0
            for idx, col in enumerate(proj.colunas):
                col_progress_pct = idx / (num_cols - 1)
                weighted_sum += len(col.cards) * col_progress_pct
            progress = int((weighted_sum / total_cards) * 100)
        else:
            progress = 0

        done_cards = 0
        if proj.colunas:
            last_col = proj.colunas[-1]
            done_cards = len(last_col.cards)
        projects_with_stats.append({
            "project": proj,
            "total_cards": total_cards,
            "done_cards": done_cards,
            "progress": progress
        })

    return templates.TemplateResponse("kanban/index.html", {
        "request": request,
        "user": current_user,
        "projects_with_stats": projects_with_stats,
        "ver_arquivados": ver_arquivados
    })

@router.get("/projetos/novo", response_class=HTMLResponse)
async def new_project_form(
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)],
    _: None = Depends(check_kanban_enabled)
):
    users = await user_crud.user.get_multi(db, limit=200)
    return templates.TemplateResponse("kanban/project_form.html", {
        "request": request,
        "user": current_user,
        "users": users,
        "project": None
    })

@router.post("/projetos/novo")
async def create_project_submit(
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)],
    _: None = Depends(check_kanban_enabled),
    titulo: str = Form(...),
    descricao: Optional[str] = Form(None),
    participante_ids: List[int] = Form([])
):
    project = await crud_kanban.create_project(
        db=db,
        titulo=titulo,
        descricao=descricao,
        criador_id=current_user.id,
        participant_ids=participante_ids
    )
    return RedirectResponse(url=f"/kanban/projetos/{project.id}", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/projetos/{project_id}", response_class=HTMLResponse)
async def view_project_board(
    request: Request,
    project_id: int,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)],
    _: None = Depends(check_kanban_enabled)
):
    project = await crud_kanban.get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado.")
    
    if not user_can_access_project(current_user, project):
        raise HTTPException(status_code=403, detail="Acesso não autorizado a este projeto.")

    users = await user_crud.user.get_multi(db, limit=200)
    
    # Load assets list for linking in cards
    assets_stmt = select(Asset).where(Asset.status != "BAIXADO").order_by(Asset.nome)
    assets_res = await db.execute(assets_stmt)
    all_assets = list(assets_res.scalars().all())

    # Calculate gradual progress for this board
    total_cards = sum(len(col.cards) for col in project.colunas)
    num_cols = len(project.colunas)
    if total_cards > 0 and num_cols > 1:
        weighted_sum = 0
        for idx, col in enumerate(project.colunas):
            col_progress_pct = idx / (num_cols - 1)
            weighted_sum += len(col.cards) * col_progress_pct
        board_progress = int((weighted_sum / total_cards) * 100)
    else:
        board_progress = 0

    # Build per-column progress map (for card badges)
    col_progress_map = {}
    for idx, col in enumerate(project.colunas):
        if num_cols > 1:
            col_progress_map[col.id] = int((idx / (num_cols - 1)) * 100)
        else:
            col_progress_map[col.id] = 0

    return templates.TemplateResponse("kanban/board.html", {
        "request": request,
        "user": current_user,
        "project": project,
        "users": users,
        "all_assets": all_assets,
        "board_progress": board_progress,
        "total_cards": total_cards,
        "col_progress_map": col_progress_map
    })

@router.get("/projetos/{project_id}/editar", response_class=HTMLResponse)
async def edit_project_form(
    request: Request,
    project_id: int,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)],
    _: None = Depends(check_kanban_enabled)
):
    project = await crud_kanban.get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado.")
    
    if not user_can_access_project(current_user, project):
        raise HTTPException(status_code=403, detail="Acesso não autorizado a este projeto.")

    users = await user_crud.user.get_multi(db, limit=200)
    return templates.TemplateResponse("kanban/project_form.html", {
        "request": request,
        "user": current_user,
        "project": project,
        "users": users
    })

@router.post("/projetos/{project_id}/editar")
async def edit_project_submit(
    request: Request,
    project_id: int,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)],
    _: None = Depends(check_kanban_enabled),
    titulo: str = Form(...),
    descricao: Optional[str] = Form(None),
    participante_ids: List[int] = Form([]),
    is_active: Optional[str] = Form(None),
    is_archived: Optional[str] = Form(None)
):
    project = await crud_kanban.get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado.")
    
    if not user_can_access_project(current_user, project):
        raise HTTPException(status_code=403, detail="Acesso negado.")

    active_bool = (is_active == "on")
    archived_bool = (is_archived == "on")

    await crud_kanban.update_project(
        db=db,
        project=project,
        titulo=titulo,
        descricao=descricao,
        participant_ids=participante_ids,
        is_active=active_bool,
        is_archived=archived_bool
    )
    return RedirectResponse(url=f"/kanban/projetos/{project_id}", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/projetos/{project_id}/status")
async def toggle_project_status(
    project_id: int,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)],
    _: None = Depends(check_kanban_enabled),
    acao: str = Form(...) # archive, unarchive, deactivate, activate
):
    project = await crud_kanban.get_project_by_id(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Projeto não encontrado.")
    
    if acao == "archive":
        project.is_archived = True
    elif acao == "unarchive":
        project.is_archived = False
    elif acao == "deactivate":
        project.is_active = False
    elif acao == "activate":
        project.is_active = True
        project.is_archived = False

    await db.commit()
    return RedirectResponse(url="/kanban", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/projetos/{project_id}/colunas/nova")
async def add_column_submit(
    project_id: int,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)],
    _: None = Depends(check_kanban_enabled),
    nome: str = Form(...),
    cor: str = Form("#6B7280")
):
    await crud_kanban.add_column(db, project_id=project_id, nome=nome, cor=cor)
    return RedirectResponse(url=f"/kanban/projetos/{project_id}", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/cards/novo")
async def create_card_submit(
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)],
    _: None = Depends(check_kanban_enabled),
    project_id: int = Form(...),
    column_id: int = Form(...),
    titulo: str = Form(...),
    descricao: Optional[str] = Form(None),
    responsavel_id: Optional[int] = Form(None),
    prioridade: str = Form("media"),
    data_entrega: Optional[str] = Form(None),
    participante_ids: List[int] = Form([]),
    ativo_ids: List[int] = Form([])
):
    due_dt = datetime.strptime(data_entrega, "%Y-%m-%d") if data_entrega else None
    resp_id = responsavel_id if (responsavel_id and responsavel_id > 0) else None

    card = await crud_kanban.create_card(
        db=db,
        project_id=project_id,
        column_id=column_id,
        titulo=titulo,
        descricao=descricao,
        criador_id=current_user.id,
        responsavel_id=resp_id,
        assignee_ids=participante_ids,
        asset_ids=ativo_ids,
        prioridade=prioridade,
        data_entrega=due_dt
    )

    if request.headers.get("HX-Request"):
        return templates.TemplateResponse("kanban/partials/card_item.html", {
            "request": request,
            "card": card
        })
    
    return RedirectResponse(url=f"/kanban/projetos/{project_id}", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/cards/{card_id}", response_class=HTMLResponse)
async def get_card_modal(
    request: Request,
    card_id: int,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)],
    _: None = Depends(check_kanban_enabled)
):
    # Fetch project board to get full context
    from app.models.kanban import KanbanCard
    card = await db.get(KanbanCard, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card não encontrado.")

    project = await crud_kanban.get_project_by_id(db, card.project_id)
    users = await user_crud.user.get_multi(db, limit=200)

    assets_stmt = select(Asset).where(Asset.status != "BAIXADO").order_by(Asset.nome)
    assets_res = await db.execute(assets_stmt)
    all_assets = list(assets_res.scalars().all())

    dept_res = await db.execute(select(Departamento).order_by(Departamento.nome))
    departamentos = list(dept_res.scalars().all())

    cc_res = await db.execute(select(CostCenter).order_by(CostCenter.nome))
    centros_custo = list(cc_res.scalars().all())

    stocks_res = await db.execute(
        select(MaterialStock).options(selectinload(MaterialStock.product)).order_by(MaterialStock.id)
    )
    material_stocks = list(stocks_res.scalars().all())

    reqs_res = await db.execute(
        select(PurchaseRequest).order_by(PurchaseRequest.data_criacao.desc()).limit(50)
    )
    solicitacoes_compras = list(reqs_res.scalars().all())

    # Find target card from board's eager loaded structure
    target_card = None
    for col in project.colunas:
        for c in col.cards:
            if c.id == card_id:
                target_card = c
                break

    return templates.TemplateResponse("kanban/partials/card_modal.html", {
        "request": request,
        "user": current_user,
        "card": target_card or card,
        "project": project,
        "users": users,
        "all_assets": all_assets,
        "departamentos": departamentos,
        "centros_custo": centros_custo,
        "material_stocks": material_stocks,
        "solicitacoes_compras": solicitacoes_compras
    })

@router.post("/cards/{card_id}/editar")
async def update_card_submit(
    request: Request,
    card_id: int,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)],
    _: None = Depends(check_kanban_enabled),
    titulo: str = Form(...),
    descricao: Optional[str] = Form(None),
    column_id: int = Form(...),
    responsavel_id: Optional[int] = Form(None),
    prioridade: str = Form("media"),
    data_entrega: Optional[str] = Form(None),
    participante_ids: List[int] = Form([]),
    ativo_ids: List[int] = Form([])
):
    from app.models.kanban import KanbanCard
    card = await db.get(KanbanCard, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card não encontrado.")

    due_dt = datetime.strptime(data_entrega, "%Y-%m-%d") if data_entrega else None
    resp_id = responsavel_id if (responsavel_id and responsavel_id > 0) else None

    updated_card = await crud_kanban.update_card(
        db=db,
        card=card,
        titulo=titulo,
        descricao=descricao,
        column_id=column_id,
        responsavel_id=resp_id,
        assignee_ids=participante_ids,
        asset_ids=ativo_ids,
        prioridade=prioridade,
        data_entrega=due_dt
    )

    return RedirectResponse(url=f"/kanban/projetos/{updated_card.project_id}", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/cards/{card_id}/mover")
async def move_card_submit(
    card_id: int,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)],
    _: None = Depends(check_kanban_enabled),
    column_id: int = Form(...),
    ordem: int = Form(0)
):
    await crud_kanban.move_card(db, card_id=card_id, target_column_id=column_id, target_order=ordem)
    return {"status": "ok", "card_id": card_id, "column_id": column_id}

@router.post("/cards/{card_id}/deletar")
async def delete_card_submit(
    card_id: int,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)],
    _: None = Depends(check_kanban_enabled)
):
    from app.models.kanban import KanbanCard
    card = await db.get(KanbanCard, card_id)
    if card:
        project_id = card.project_id
        await crud_kanban.delete_card(db, card)
        return RedirectResponse(url=f"/kanban/projetos/{project_id}", status_code=status.HTTP_303_SEE_OTHER)
    return RedirectResponse(url="/kanban", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/cards/{card_id}/anexo")
async def upload_attachment_submit(
    request: Request,
    card_id: int,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)],
    _: None = Depends(check_kanban_enabled),
    tipo_anexo: str = Form("imagem"), # imagem, link, arquivo
    link_url: Optional[str] = Form(None),
    nome_anexo: Optional[str] = Form(None),
    arquivo: Optional[UploadFile] = File(None)
):
    from app.models.kanban import KanbanCard
    card = await db.get(KanbanCard, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card não encontrado.")

    if tipo_anexo == "link" and link_url:
        final_nome = nome_anexo or link_url
        await crud_kanban.add_attachment(db, card_id=card_id, nome=final_nome, tipo="link", url=link_url)
    elif arquivo and arquivo.filename:
        from app.core.security_utils import validate_uploaded_file, generate_safe_filename, ALLOWED_DOCUMENT_EXTENSIONS
        ext = validate_uploaded_file(arquivo, allowed_extensions=ALLOWED_DOCUMENT_EXTENSIONS)
        upload_dir = os.path.join("static", "uploads", "kanban")
        os.makedirs(upload_dir, exist_ok=True)
        
        unique_name = generate_safe_filename(ext, prefix="kanban")
        filepath = os.path.join(upload_dir, unique_name)
        
        content = await arquivo.read()
        with open(filepath, "wb") as f:
            f.write(content)
            
        file_url = f"/static/uploads/kanban/{unique_name}"
        att_type = "imagem" if ext.lower() in [".png", ".jpg", ".jpeg", ".webp", ".gif"] else "arquivo"
        safe_orig_name = os.path.basename(arquivo.filename)
        await crud_kanban.add_attachment(db, card_id=card_id, nome=safe_orig_name, tipo=att_type, url=file_url)


    return RedirectResponse(url=f"/kanban/cards/{card_id}", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/anexos/{attachment_id}/deletar")
async def delete_attachment_submit(
    attachment_id: int,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)],
    _: None = Depends(check_kanban_enabled)
):
    from app.models.kanban import KanbanAttachment
    att = await db.get(KanbanAttachment, attachment_id)
    card_id = att.card_id if att else None
    if att:
        await crud_kanban.remove_attachment(db, attachment_id)
    
    if card_id:
        return RedirectResponse(url=f"/kanban/cards/{card_id}", status_code=status.HTTP_303_SEE_OTHER)
    return RedirectResponse(url="/kanban", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/cards/{card_id}/solicitar-compra")
async def create_purchase_request_from_card(
    card_id: int,
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)],
    _: None = Depends(check_kanban_enabled),
    tipo_item: str = Form(...),
    nome_produto: str = Form(...),
    quantidade: float = Form(1.0),
    valor_estimado: float = Form(0.0),
    departamento_id: Optional[int] = Form(None),
    centro_custo_id: Optional[int] = Form(None),
    justificativa: Optional[str] = Form(None)
):
    from app.models.kanban import KanbanCard
    card = await db.get(KanbanCard, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card não encontrado.")

    # 1. Categoria
    cat_stmt = select(PurchaseCategory).limit(1)
    cat_res = await db.execute(cat_stmt)
    cat = cat_res.scalars().first()
    if not cat:
        cat = PurchaseCategory(nome="TI / Suprimentos", descricao="Categoria padrão TI", ativo=True)
        db.add(cat)
        await db.flush()

    # 2. Produto
    prod_stmt = select(PurchaseProduct).where(PurchaseProduct.nome == nome_produto.strip()).limit(1)
    prod_res = await db.execute(prod_stmt)
    prod = prod_res.scalars().first()
    if not prod:
        prod_type = ProductType.MATERIAL_CONSUMO if tipo_item == "Consumo" else ProductType.EQUIPAMENTO
        prod_code = f"PROD-KB-{uuid.uuid4().hex[:6].upper()}"
        prod = PurchaseProduct(
            codigo=prod_code,
            nome=nome_produto.strip(),
            categoria_id=cat.id,
            tipo=prod_type,
            unidade="UN",
            ativo=True
        )
        db.add(prod)
        await db.flush()

    # 3. Departamento e Centro de Custo
    dept_id = departamento_id
    if not dept_id:
        d_res = await db.execute(select(Departamento).limit(1))
        first_d = d_res.scalars().first()
        if not first_d:
            first_d = Departamento(nome="Tecnologia da Informação")
            db.add(first_d)
            await db.flush()
        dept_id = first_d.id

    cc_id = centro_custo_id
    if not cc_id:
        cc_res = await db.execute(select(CostCenter).limit(1))
        first_cc = cc_res.scalars().first()
        if not first_cc:
            first_cc = CostCenter(codigo="CC-TI-01", nome="TI / Operações")
            db.add(first_cc)
            await db.flush()
        cc_id = first_cc.id

    # 4. Solicitação de Compras
    num = await generate_request_number(db)
    just = justificativa or f"Solicitação de Compra gerada via Kanban (Card #{card.id}: {card.titulo})"
    
    req = PurchaseRequest(
        numero=num,
        solicitante_id=current_user.id,
        departamento_id=dept_id,
        centro_custo_id=cc_id,
        justificativa=just,
        urgencia="Alta" if card.prioridade in ["alta", "urgente"] else "Média",
        status=PurchaseRequestStatus.PENDENTE
    )
    db.add(req)
    await db.flush()

    item = PurchaseRequestItem(
        request_id=req.id,
        product_id=prod.id,
        quantidade=quantidade,
        valor_estimado=valor_estimado,
        observacao=f"Item para a tarefa Kanban #{card.id}"
    )
    db.add(item)

    card.purchase_request_id = req.id
    card.tipo_item_necessario = tipo_item

    await db.commit()
    return RedirectResponse(url=f"/kanban/cards/{card_id}", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/cards/{card_id}/vincular-estoque")
async def link_stock_to_card(
    card_id: int,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)],
    _: None = Depends(check_kanban_enabled),
    stock_id: int = Form(...),
    quantidade_usar: float = Form(1.0),
    dar_baixa_estoque: Optional[bool] = Form(False)
):
    from app.models.kanban import KanbanCard
    card = await db.get(KanbanCard, card_id)
    if not card:
        raise HTTPException(status_code=404, detail="Card não encontrado.")

    stock = await db.get(MaterialStock, stock_id)
    if not stock:
        raise HTTPException(status_code=404, detail="Item de estoque não encontrado.")

    card.material_stock_id = stock.id
    card.tipo_item_necessario = "Estoque"

    if dar_baixa_estoque and quantidade_usar > 0:
        await create_or_update_stock(
            db=db,
            product_id=stock.product_id,
            quantidade=quantidade_usar,
            tipo="Saída",
            user_id=current_user.id,
            justificativa=f"Baixa/Uso de Estoque no Card Kanban #{card.id} ({card.titulo})",
            origem_tabela="kanban_cards",
            origem_id=card.id
        )

    await db.commit()
    return RedirectResponse(url=f"/kanban/cards/{card_id}", status_code=status.HTTP_303_SEE_OTHER)

