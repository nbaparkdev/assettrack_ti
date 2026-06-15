
# app/web/endpoints/assets.py
from typing import Annotated, Optional
from fastapi import APIRouter, Request, Depends, Form, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
import os
import shutil
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, datetime

from app.web.dependencies import get_active_user_web
from app.models.user import User, UserRole
from app.models.asset import AssetStatus
from app.models.location import Localizacao
from app.schemas.asset import AssetCreate, AssetUpdate
from app.models.transaction import Movimentacao, TipoMovimentacao, Solicitacao, StatusSolicitacao
from app.database import get_db
from app.crud import transaction as transaction_crud
from app.crud import asset as asset_crud
from app.crud import crud_supplier, crud_invoice
from app.crud import asset_category as asset_category_crud
from app.crud import location
from app.schemas.invoice import NotaFiscalCreate
from app.services.qr_service import QRService

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def list_assets(
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)],
    categoria_id: Optional[str] = None
):
    # Calculate stats for the header
    from sqlalchemy import func, select

    cat_id = int(categoria_id) if categoria_id and categoria_id.strip() else None

    total_assets = await db.scalar(select(func.count(asset_crud.asset.model.id)))
    available_assets = await db.scalar(select(func.count(asset_crud.asset.model.id)).filter(asset_crud.asset.model.status == AssetStatus.DISPONIVEL))
    in_use_assets = await db.scalar(select(func.count(asset_crud.asset.model.id)).filter(asset_crud.asset.model.status == AssetStatus.EM_USO))
    maintenance_assets = await db.scalar(select(func.count(asset_crud.asset.model.id)).filter(asset_crud.asset.model.status == AssetStatus.MANUTENCAO))

    if cat_id:
        from sqlalchemy.orm import selectinload
        result = await db.execute(
            select(asset_crud.asset.model)
            .options(
                selectinload(asset_crud.asset.model.current_user),
                selectinload(asset_crud.asset.model.current_departamento),
                selectinload(asset_crud.asset.model.current_local),
                selectinload(asset_crud.asset.model.current_armazenamento),
                selectinload(asset_crud.asset.model.fornecedor),
                selectinload(asset_crud.asset.model.nota_fiscal),
                selectinload(asset_crud.asset.model.categoria)
            )
            .filter(asset_crud.asset.model.categoria_id == cat_id)
        )
        assets = result.scalars().all()
    else:
        assets = await asset_crud.asset.get_multi(db)

    categories = await asset_category_crud.category.get_multi(db)

    return templates.TemplateResponse("assets/list.html", {
        "request": request,
        "user": current_user,
        "assets": assets,
        "categories": categories,
        "filters": {
            "categoria_id": str(cat_id) if cat_id else ""
        },
        "stats": {
            "total": total_assets or 0,
            "available": available_assets or 0,
            "in_use": in_use_assets or 0,
            "maintenance": maintenance_assets or 0
        },
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
    q: Optional[str] = None, # Alterado para 'q' para ser mais genérico (nome ou serial)
    current_user: Annotated[User, Depends(get_active_user_web)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
):
    """Search asset by name or serial number and redirect to detail page"""
    from sqlalchemy import select, func, or_
    from app.models.asset import Asset
    
    if not q:
        return RedirectResponse(url="/assets", status_code=303)

    result = await db.execute(
        select(Asset).where(
            or_(
                Asset.e_patrimonio.ilike(f"%{q}%"),
                Asset.nome.ilike(f"%{q}%")
            )
        )
    )
    assets_found = result.scalars().all()

    # Se encontrou exatamente um, vai direto para o detalhe
    if len(assets_found) == 1:
        asset = assets_found[0]
        return RedirectResponse(url=f"/assets/ep/{asset.e_patrimonio}", status_code=303)

    # Se encontrou varios ou nenhum, mostra a lista filtrada
    total_assets = await db.scalar(select(func.count(Asset.id)))
    available_assets = await db.scalar(select(func.count(Asset.id)).filter(Asset.status == AssetStatus.DISPONIVEL))
    in_use_assets = await db.scalar(select(func.count(Asset.id)).filter(Asset.status == AssetStatus.EM_USO))
    maintenance_assets = await db.scalar(select(func.count(Asset.id)).filter(Asset.status == AssetStatus.MANUTENCAO))

    categories = await asset_category_crud.category.get_multi(db)

    return templates.TemplateResponse("assets/list.html", {
        "request": request,
        "user": current_user,
        "assets": assets_found,
        "categories": categories,
        "stats": {
            "total": total_assets or 0,
            "available": available_assets or 0,
            "in_use": in_use_assets or 0,
            "maintenance": maintenance_assets or 0
        },
        "query": q,
        "title": f"Busca: {q}"
    })

@router.get("/new", response_class=HTMLResponse)
async def new_asset_form(
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    fornecedores = await crud_supplier.get_fornecedores(db)
    categories = await asset_category_crud.category.get_multi(db)
    locais = await location.localizacao.get_multi(db)
    return templates.TemplateResponse("assets/form.html", {
        "request": request,
        "user": current_user,
        "fornecedores": fornecedores,
        "categories": categories,
        "locais": locais,
        "title": "Novo Ativo"
    })

@router.post("/new", response_class=HTMLResponse)
async def create_asset(
    request: Request,
    nome: Annotated[str, Form()],
    modelo: Annotated[str, Form()],
    e_patrimonio: Annotated[str, Form()],
    descricao: Annotated[Optional[str], Form()] = None,
    data_aquisicao: Annotated[Optional[str], Form()] = None,
    valor_aquisicao: Annotated[Optional[str], Form()] = None,
    numero_serie: Annotated[Optional[str], Form()] = None,
    fornecedor_id: Annotated[Optional[int], Form()] = None,
    nota_fiscal_id: Annotated[Optional[int], Form()] = None,
    categoria_id: Annotated[Optional[int], Form()] = None,
    current_local_id: Annotated[Optional[str], Form()] = None,
    em_posse_de: Annotated[Optional[str], Form()] = None,
    foto: Annotated[Optional[UploadFile], File()] = None,
    current_user: Annotated[User, Depends(get_active_user_web)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
):
    try:
        # Convert empty string form values to proper types
        local_id = int(current_local_id) if current_local_id and current_local_id.strip() else None

        # Handle empty strings from form
        dt_aquisicao = None
        if data_aquisicao:
            try:
                dt_aquisicao = datetime.strptime(data_aquisicao, "%Y-%m-%d")
            except ValueError:
                dt_aquisicao = None

        val_aquisicao = None
        if valor_aquisicao and valor_aquisicao.strip():
            try:
                # Handle Brazilian currency format (1.200,50 -> 1200.50)
                clean_value = valor_aquisicao.replace('.', '').replace(',', '.') if ',' in valor_aquisicao and '.' in valor_aquisicao else valor_aquisicao.replace(',', '.')
                val_aquisicao = float(clean_value)
            except ValueError:
                raise ValueError(f"Valor inválido: {valor_aquisicao}")

        foto_path = None
        if foto and foto.filename:
            upload_dir = "static/uploads"
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, f"{e_patrimonio}_{foto.filename}")
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(foto.file, buffer)
            foto_path = f"/{file_path}"

        asset_in = AssetCreate(
            nome=nome,
            modelo=modelo,
            e_patrimonio=e_patrimonio,
            descricao=descricao,
            data_aquisicao=dt_aquisicao,
            valor=val_aquisicao,
            numero_serie=numero_serie,
            fornecedor_id=fornecedor_id,
            nota_fiscal_id=nota_fiscal_id,
            categoria_id=categoria_id,
            current_local_id=local_id,
            em_posse_de=em_posse_de if em_posse_de else None,
            foto_path=foto_path,
            created_by_id=current_user.id if current_user else None,
            status=AssetStatus.DISPONIVEL
        )
        await asset_crud.asset.create(db, obj_in=asset_in)
        return RedirectResponse(url="/assets", status_code=303)
    except Exception as e:
        fornecedores = await crud_supplier.get_fornecedores(db)
        categories = await asset_category_crud.category.get_multi(db)
        locais = await location.localizacao.get_multi(db)
        return templates.TemplateResponse("assets/form.html", {
            "request": request,
            "user": current_user,
            "fornecedores": fornecedores,
            "categories": categories,
            "locais": locais,
            "error": f"Erro ao criar ativo: {str(e)}",
            "title": "Novo Ativo"
        })


# --- Asset Categories Admin ---

@router.get("/admin/categorias", response_class=HTMLResponse)
async def list_categories(
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    user_role = str(current_user.role.value).lower()
    if user_role not in [UserRole.ADMIN, UserRole.GERENTE, UserRole.GERENTE_INFRA]:
        return RedirectResponse(url="/assets", status_code=303)

    categories = await asset_category_crud.category.get_multi(db)
    return templates.TemplateResponse("assets/admin/categories.html", {
        "request": request,
        "user": current_user,
        "categories": categories,
        "title": "Categorias de Ativos"
    })


@router.post("/admin/categorias")
async def create_category(
    nome: Annotated[str, Form()],
    descricao: Annotated[Optional[str], Form()] = None,
    current_user: Annotated[User, Depends(get_active_user_web)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
):
    user_role = str(current_user.role.value).lower()
    if user_role not in [UserRole.ADMIN, UserRole.GERENTE, UserRole.GERENTE_INFRA]:
        raise HTTPException(status_code=403)

    from app.schemas.asset_category import AssetCategoryCreate
    cat_in = AssetCategoryCreate(nome=nome, descricao=descricao)
    await asset_category_crud.category.create(db, obj_in=cat_in)
    return RedirectResponse(url="/assets/admin/categorias", status_code=303)


@router.post("/admin/categorias/{cat_id}/delete")
async def delete_category(
    cat_id: int,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    user_role = str(current_user.role.value).lower()
    if user_role not in [UserRole.ADMIN, UserRole.GERENTE, UserRole.GERENTE_INFRA]:
        raise HTTPException(status_code=403)

    await asset_category_crud.category.remove(db, id=cat_id)
    return RedirectResponse(url="/assets/admin/categorias", status_code=303)


# --- Asset Reports ---

@router.get("/reports", response_class=HTMLResponse)
async def reports_page(
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)],
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    nome: Optional[str] = None,
    categoria_id: Optional[str] = None,
    fornecedor_id: Optional[str] = None,
    nfe: Optional[str] = None,
    patrimonio: Optional[str] = None
):
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from app.models.invoice import NotaFiscal

    # Convert empty string params to int
    cat_id = int(categoria_id) if categoria_id and categoria_id.strip() else None
    forn_id = int(fornecedor_id) if fornecedor_id and fornecedor_id.strip() else None

    categories = await asset_category_crud.category.get_multi(db)
    fornecedores = await crud_supplier.get_fornecedores(db)

    query = select(asset_crud.asset.model).options(
        selectinload(asset_crud.asset.model.categoria),
        selectinload(asset_crud.asset.model.fornecedor),
        selectinload(asset_crud.asset.model.nota_fiscal)
    )

    has_filters = False
    active_filters = []

    if data_inicio:
        try:
            dt = datetime.strptime(data_inicio, "%Y-%m-%d")
            query = query.filter(asset_crud.asset.model.data_aquisicao >= dt)
            has_filters = True
            active_filters.append(f"Data inicio: {data_inicio}")
        except ValueError:
            pass

    if data_fim:
        try:
            dt = datetime.strptime(data_fim, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
            query = query.filter(asset_crud.asset.model.data_aquisicao <= dt)
            has_filters = True
            active_filters.append(f"Data fim: {data_fim}")
        except ValueError:
            pass

    if nome:
        query = query.filter(asset_crud.asset.model.nome.ilike(f"%{nome}%"))
        has_filters = True
        active_filters.append(f"Nome: {nome}")

    if cat_id:
        query = query.filter(asset_crud.asset.model.categoria_id == cat_id)
        has_filters = True
        cat = next((c for c in categories if c.id == cat_id), None)
        active_filters.append(f"Categoria: {cat.nome if cat else cat_id}")

    if forn_id:
        query = query.filter(asset_crud.asset.model.fornecedor_id == forn_id)
        has_filters = True
        fornecedor = next((f for f in fornecedores if f.id == forn_id), None)
        active_filters.append(f"Fornecedor: {fornecedor.nome if fornecedor else forn_id}")

    if nfe:
        query = query.join(NotaFiscal).filter(NotaFiscal.numero_nota.ilike(f"%{nfe}%"))
        has_filters = True
        active_filters.append(f"NFe: {nfe}")

    if patrimonio:
        query = query.filter(asset_crud.asset.model.e_patrimonio.ilike(f"%{patrimonio}%"))
        has_filters = True
        active_filters.append(f"Patrimonio: {patrimonio}")

    result = await db.execute(query)
    assets = result.scalars().all()

    return templates.TemplateResponse("assets/reports.html", {
        "request": request,
        "user": current_user,
        "assets": assets,
        "categories": categories,
        "fornecedores": fornecedores,
        "has_filters": has_filters,
        "filtros": {
            "data_inicio": data_inicio or "",
            "data_fim": data_fim or "",
            "nome": nome or "",
            "categoria_id": cat_id or "",
            "fornecedor_id": forn_id or "",
            "nfe": nfe or "",
            "patrimonio": patrimonio or ""
        },
        "title": "Relatorio de Ativos"
    })


@router.get("/reports/pdf")
async def reports_pdf(
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)],
    data_inicio: Optional[str] = None,
    data_fim: Optional[str] = None,
    nome: Optional[str] = None,
    categoria_id: Optional[str] = None,
    fornecedor_id: Optional[str] = None,
    nfe: Optional[str] = None,
    patrimonio: Optional[str] = None
):
    from weasyprint import HTML
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from app.models.invoice import NotaFiscal

    cat_id = int(categoria_id) if categoria_id and categoria_id.strip() else None
    forn_id = int(fornecedor_id) if fornecedor_id and fornecedor_id.strip() else None

    query = select(asset_crud.asset.model).options(
        selectinload(asset_crud.asset.model.categoria),
        selectinload(asset_crud.asset.model.fornecedor),
        selectinload(asset_crud.asset.model.nota_fiscal)
    )

    has_filters = False
    active_filters = []

    if data_inicio:
        try:
            dt = datetime.strptime(data_inicio, "%Y-%m-%d")
            query = query.filter(asset_crud.asset.model.data_aquisicao >= dt)
            has_filters = True
            active_filters.append(f"Data inicio: {data_inicio}")
        except ValueError:
            pass

    if data_fim:
        try:
            dt = datetime.strptime(data_fim, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
            query = query.filter(asset_crud.asset.model.data_aquisicao <= dt)
            has_filters = True
            active_filters.append(f"Data fim: {data_fim}")
        except ValueError:
            pass

    if nome:
        query = query.filter(asset_crud.asset.model.nome.ilike(f"%{nome}%"))
        has_filters = True
        active_filters.append(f"Nome: {nome}")

    if cat_id:
        query = query.filter(asset_crud.asset.model.categoria_id == cat_id)
        has_filters = True

    if forn_id:
        query = query.filter(asset_crud.asset.model.fornecedor_id == forn_id)
        has_filters = True

    if nfe:
        query = query.join(NotaFiscal).filter(NotaFiscal.numero_nota.ilike(f"%{nfe}%"))
        has_filters = True
        active_filters.append(f"NFe: {nfe}")

    if patrimonio:
        query = query.filter(asset_crud.asset.model.e_patrimonio.ilike(f"%{patrimonio}%"))
        has_filters = True
        active_filters.append(f"Patrimonio: {patrimonio}")

    result = await db.execute(query)
    assets = result.scalars().all()

    html_content = templates.get_template("assets/reports_pdf.html").render({
        "request": request,
        "assets": assets,
        "has_filters": has_filters,
        "active_filters": " | ".join(active_filters) if active_filters else "",
        "generated_at": datetime.now().strftime("%d/%m/%Y %H:%M")
    })

    pdf_bytes = HTML(string=html_content).write_pdf()

    filename = f"relatorio_ativos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/qrcode/{asset_id}")
async def get_asset_qrcode_web(
    request: Request,
    asset_id: int,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Gera QR Code para o ativo (autenticação via cookie)"""
    asset = await asset_crud.asset.get(db, id=asset_id)
    if not asset:
        return Response(content=b"", status_code=404)
    
    # URL completa para acessar o ativo via Serial Number
    # Usando o host configurado ou localhost como padrão
    base_url = str(request.base_url).rstrip('/')
    qr_content = f"{base_url}/assets/ep/{asset.e_patrimonio}"
    img_io = QRService.generate_qr_code(qr_content)
    
    return Response(content=img_io.getvalue(), media_type="image/png")

@router.get("/ep/{e_patrimonio}", response_class=HTMLResponse)
async def asset_detail_by_serial(
    request: Request,
    e_patrimonio: str,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Visualiza detalhes do ativo buscando pelo Serial Number (S/N)"""
    asset = await asset_crud.asset.get_by_e_patrimonio(db, e_patrimonio=e_patrimonio)
    if not asset:
        return RedirectResponse(url="/assets?error=Ativo+nao+encontrado", status_code=303)
    
    # Reutiliza a lógica de detalhe
    return await asset_detail(request, asset.id, current_user, db)

@router.get("/{asset_id}", response_class=HTMLResponse)
async def asset_detail(
    request: Request,
    asset_id: int,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    asset = await asset_crud.asset.get(db, id=asset_id)
    if not asset:
        from sqlalchemy import select, func
        from app.models.asset import Asset

        total_assets = await db.scalar(select(func.count(Asset.id)))
        available_assets = await db.scalar(select(func.count(Asset.id)).filter(Asset.status == AssetStatus.DISPONIVEL))
        in_use_assets = await db.scalar(select(func.count(Asset.id)).filter(Asset.status == AssetStatus.EM_USO))
        maintenance_assets = await db.scalar(select(func.count(Asset.id)).filter(Asset.status == AssetStatus.MANUTENCAO))

        assets = await asset_crud.asset.get_multi(db)
        return templates.TemplateResponse("assets/list.html", {
            "request": request,
            "user": current_user,
            "assets": assets,
            "stats": {
                "total": total_assets or 0,
                "available": available_assets or 0,
                "in_use": in_use_assets or 0,
                "maintenance": maintenance_assets or 0
            },
            "error": f"Ativo com ID {asset_id} não encontrado.",
            "title": "Ativos"
        })

    # Fetch history
    from sqlalchemy import select
    from app.models.transaction import Movimentacao, Solicitacao
    from app.models.maintenance import Manutencao
    
    # 1. Movimentações
    mov_result = await db.execute(
        select(Movimentacao)
        .filter(Movimentacao.asset_id == asset_id)
        .order_by(Movimentacao.data.desc())
        .limit(10)
    )
    history_movimentacoes = mov_result.scalars().all()

    # 2. Solicitações
    sol_result = await db.execute(
        select(Solicitacao)
        .filter(Solicitacao.asset_id == asset_id)
        .order_by(Solicitacao.data_solicitacao.desc())
        .limit(10)
    )
    history_solicitacoes = sol_result.scalars().all()

    # 3. Manutenções
    man_result = await db.execute(
        select(Manutencao)
        .filter(Manutencao.asset_id == asset_id)
        .order_by(Manutencao.data_entrada.desc())
        .limit(10)
    )
    history_manutencoes = man_result.scalars().all()
        
    return templates.TemplateResponse("assets/detail.html", {
        "request": request,
        "user": current_user,
        "asset": asset,
        "history_movimentacoes": history_movimentacoes,
        "history_solicitacoes": history_solicitacoes,
        "history_manutencoes": history_manutencoes,
        "title": f"Ativo: {asset.nome}"
    })

@router.get("/ep/{e_patrimonio}/edit", response_class=HTMLResponse)
async def edit_asset_form_by_serial(
    request: Request,
    e_patrimonio: str,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    """Acessa formulário de edição buscando pelo Serial Number (S/N)"""
    asset = await asset_crud.asset.get_by_e_patrimonio(db, e_patrimonio=e_patrimonio)
    if not asset:
        return RedirectResponse(url="/assets?error=Ativo+nao+encontrado", status_code=303)
    
    return await edit_asset_form(request, asset.id, current_user, db)

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

    fornecedores = await crud_supplier.get_fornecedores(db)
    categories = await asset_category_crud.category.get_multi(db)
    locais = await location.localizacao.get_multi(db)

    return templates.TemplateResponse("assets/form.html", {
        "request": request,
        "user": current_user,
        "asset": asset,
        "fornecedores": fornecedores,
        "categories": categories,
        "locais": locais,
        "title": f"Editar Ativo: {asset.nome}"
    })

@router.post("/{asset_id}/edit", response_class=HTMLResponse)
async def update_asset(
    request: Request,
    asset_id: int,
    nome: Annotated[str, Form()],
    modelo: Annotated[str, Form()],
    e_patrimonio: Annotated[str, Form()],
    descricao: Annotated[Optional[str], Form()] = None,
    data_aquisicao: Annotated[Optional[str], Form()] = None,
    valor_aquisicao: Annotated[Optional[str], Form()] = None,
    numero_serie: Annotated[Optional[str], Form()] = None,
    fornecedor_id: Annotated[Optional[int], Form()] = None,
    nota_fiscal_id: Annotated[Optional[int], Form()] = None,
    categoria_id: Annotated[Optional[int], Form()] = None,
    current_local_id: Annotated[Optional[str], Form()] = None,
    em_posse_de: Annotated[Optional[str], Form()] = None,
    foto: Annotated[Optional[UploadFile], File()] = None,
    current_user: Annotated[User, Depends(get_active_user_web)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
):
    if current_user.role not in [UserRole.ADMIN, UserRole.GERENTE]:
        return RedirectResponse(url=f"/assets/{asset_id}", status_code=303)

    asset = await asset_crud.asset.get(db, id=asset_id)
    if not asset:
         return RedirectResponse(url="/assets", status_code=303)

    try:
        # Convert empty string form values to proper types
        local_id = int(current_local_id) if current_local_id and current_local_id.strip() else None

        # Handle empty strings from form
        dt_aquisicao = None
        if data_aquisicao:
            try:
                dt_aquisicao = datetime.strptime(data_aquisicao, "%Y-%m-%d")
            except ValueError:
                dt_aquisicao = None
        
        val_aquisicao = None
        if valor_aquisicao and valor_aquisicao.strip():
            try:
                clean_value = valor_aquisicao.replace('.', '').replace(',', '.') if ',' in valor_aquisicao and '.' in valor_aquisicao else valor_aquisicao.replace(',', '.')
                val_aquisicao = float(clean_value)
            except ValueError:
                raise ValueError(f"Valor inválido: {valor_aquisicao}")

        # nota_fiscal_id is now passed directly from the form select
        
        foto_path = asset.foto_path
        if foto and foto.filename:
            upload_dir = "static/uploads"
            os.makedirs(upload_dir, exist_ok=True)
            file_path = os.path.join(upload_dir, f"{e_patrimonio}_{foto.filename}")
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(foto.file, buffer)
            foto_path = f"/{file_path}"

        asset_update = AssetUpdate(
            nome=nome,
            modelo=modelo,
            e_patrimonio=e_patrimonio,
            descricao=descricao if descricao else None,
            data_aquisicao=dt_aquisicao,
            valor=val_aquisicao,
            numero_serie=numero_serie,
            fornecedor_id=fornecedor_id,
            nota_fiscal_id=nota_fiscal_id,
            categoria_id=categoria_id,
            current_local_id=local_id,
            em_posse_de=em_posse_de if em_posse_de else None,
            foto_path=foto_path
        )
        await asset_crud.asset.update(db, db_obj=asset, obj_in=asset_update)
        return RedirectResponse(url=f"/assets/{asset_id}", status_code=303)
    except Exception as e:
        fornecedores = await crud_supplier.get_fornecedores(db)
        categories = await asset_category_crud.category.get_multi(db)
        locais = await location.localizacao.get_multi(db)
        return templates.TemplateResponse("assets/form.html", {
            "request": request,
            "user": current_user,
            "asset": asset,
            "fornecedores": fornecedores,
            "categories": categories,
            "locais": locais,
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


# --- Location Management ---

@router.get("/admin/localizacoes", response_class=HTMLResponse)
async def list_locais(
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    user_role = str(current_user.role.value).lower()
    if user_role not in [UserRole.ADMIN, UserRole.GERENTE, UserRole.GERENTE_INFRA]:
        return RedirectResponse(url="/assets", status_code=303)

    from sqlalchemy.orm import selectinload
    from sqlalchemy import select
    result = await db.execute(
        select(Localizacao).options(selectinload(Localizacao.assets), selectinload(Localizacao.departamento))
    )
    locais_list = result.scalars().all()
    departamentos_list = await location.departamento.get_multi(db)

    return templates.TemplateResponse("assets/admin/locais.html", {
        "request": request,
        "user": current_user,
        "locais": locais_list,
        "departamentos": departamentos_list,
        "title": "Localizações"
    })


@router.post("/admin/localizacoes")
async def create_local(
    nome: Annotated[str, Form()],
    departamento_id: Annotated[Optional[int], Form()] = None,
    current_user: Annotated[User, Depends(get_active_user_web)] = None,
    db: Annotated[AsyncSession, Depends(get_db)] = None
):
    user_role = str(current_user.role.value).lower()
    if user_role not in [UserRole.ADMIN, UserRole.GERENTE, UserRole.GERENTE_INFRA]:
        return RedirectResponse(url="/assets", status_code=303)

    from app.schemas.location import LocalizacaoCreate
    local_in = LocalizacaoCreate(nome=nome, departamento_id=departamento_id)
    await location.localizacao.create(db, obj_in=local_in)
    return RedirectResponse(url="/assets/admin/localizacoes", status_code=303)


@router.post("/admin/localizacoes/{local_id}/delete")
async def delete_local(
    local_id: int,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    user_role = str(current_user.role.value).lower()
    if user_role not in [UserRole.ADMIN, UserRole.GERENTE, UserRole.GERENTE_INFRA]:
        return RedirectResponse(url="/assets", status_code=303)

    try:
        await location.localizacao.remove(db, id=local_id)
        return RedirectResponse(url="/assets/admin/localizacoes", status_code=303)
    except Exception as e:
        await db.rollback()
        from sqlalchemy.orm import selectinload
        from sqlalchemy import select
        result = await db.execute(
            select(Localizacao).options(selectinload(Localizacao.assets), selectinload(Localizacao.departamento))
        )
        locais_list = result.scalars().all()
        departamentos_list = await location.departamento.get_multi(db)

        error_msg = f"Erro ao excluir: {str(e)}"
        if "constraint" in str(e).lower() or "foreign" in str(e).lower():
            error_msg = "Não é possível excluir esta localização pois há ativos vinculados a ela."

        return templates.TemplateResponse("assets/admin/locais.html", {
            "request": request,
            "user": current_user,
            "locais": locais_list,
            "departamentos": departamentos_list,
            "error": error_msg,
            "title": "Localizações"
        })
