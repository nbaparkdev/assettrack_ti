# app/web/endpoints/procurement.py
from typing import Annotated, Optional, List
from fastapi import APIRouter, Request, Depends, Form, HTTPException, status, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, and_
from sqlalchemy.orm import selectinload
import logging
from datetime import datetime
from app.core.datetime_utils import now_sp
from decimal import Decimal

from app.database import get_db
from app.web.dependencies import get_active_user_web, check_purchases_enabled
from app.models.user import User, UserRole
from app.models.supplier import Fornecedor
from app.models.invoice import NotaFiscal
from app.models.procurement import (
    PurchaseRequest, PurchaseRequestItem, PurchaseQuotation, PurchaseQuotationSupplier,
    PurchaseQuotationItem, PurchaseOrder, PurchaseOrderItem, PurchaseReceiving,
    PurchaseReceivingItem, PurchaseCategory, PurchaseProduct, CostCenter,
    ProductType, MaterialStock, MaterialStockTransaction, PurchaseRequestStatus,
    PurchaseOrderStatus, PurchaseApproval, PurchaseContract,
    PurchaseResearch, PurchaseResearchItem, PurchaseResearchStatus
)
from app.crud import procurement as crud_proc
from app.services import procurement_service as serv_proc
from app.schemas.procurement import (
    PurchaseRequestCreate, PurchaseRequestItemCreate,
    PurchaseOrderCreate, PurchaseOrderItemCreate,
    PurchaseReceivingCreate, PurchaseReceivingItemCreate,
    PurchaseProductCreate, PurchaseProductUpdate, CostCenterCreate, PurchaseContractCreate, PurchaseContractUpdate,
    PurchaseCategoryCreate, PurchaseResearchCreate, PurchaseResearchItemCreate
)

router = APIRouter(dependencies=[Depends(check_purchases_enabled)])
templates = Jinja2Templates(directory="app/templates")
logger = logging.getLogger(__name__)

# ---------
# DASHBOARD
# ---------
@router.get("/", response_class=HTMLResponse)
async def dashboard_compras(
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    # Stats
    req_pending_count = await db.scalar(
        select(func.count(PurchaseRequest.id)).where(PurchaseRequest.status == PurchaseRequestStatus.PENDENTE)
    )
    orders_active_count = await db.scalar(
        select(func.count(PurchaseOrder.id)).where(PurchaseOrder.status == PurchaseOrderStatus.ABERTO)
    )
    low_stock_count = await db.scalar(
        select(func.count(MaterialStock.id)).where(MaterialStock.quantidade_saldo < 5)
    )
    
    # Recents
    requests_recent = await crud_proc.get_purchase_requests(db, limit=5)
    orders_recent = await crud_proc.get_purchase_orders(db, limit=5)

    return templates.TemplateResponse("procurement/dashboard.html", {
        "request": request,
        "user": current_user,
        "req_pending_count": req_pending_count or 0,
        "orders_active_count": orders_active_count or 0,
        "low_stock_count": low_stock_count or 0,
        "requests_recent": requests_recent,
        "orders_recent": orders_recent,
        "title": "Módulo de Compras"
    })

# -----------------
# PURCHASE REQUESTS
# -----------------
@router.get("/solicitacoes", response_class=HTMLResponse)
async def list_requests(
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    solicitacoes = await crud_proc.get_purchase_requests(db, limit=100)
    return templates.TemplateResponse("procurement/requests_list.html", {
        "request": request,
        "user": current_user,
        "solicitacoes": solicitacoes,
        "title": "Solicitações de Compra"
    })

@router.get("/solicitacoes/new", response_class=HTMLResponse)
async def new_request_form(
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)],
    origem_tipo: Optional[str] = None,
    origem_id: Optional[int] = None,
    descricao: Optional[str] = None,
):
    products = await crud_proc.get_products(db, limit=500)
    cost_centers = await crud_proc.get_cost_centers(db, limit=100)
    suppliers = (await db.execute(select(Fornecedor))).scalars().all()
    categories = await crud_proc.get_categories(db, limit=100)
    units = await crud_proc.get_units(db)

    # Pre-fill justification when coming from another module
    justificativa_prefill = ""
    if descricao:
        justificativa_prefill = descricao
    elif origem_tipo and origem_id:
        if origem_tipo == "manutencao":
            justificativa_prefill = f"Aquisição de peças/insumos para Manutenção #{origem_id}"
        elif origem_tipo == "chamado":
            justificativa_prefill = f"Aquisição de itens para Chamado #{origem_id}"
        elif origem_tipo == "os":
            justificativa_prefill = f"Aquisição de itens para OS #{origem_id}"

    return templates.TemplateResponse("procurement/request_form.html", {
        "request": request,
        "user": current_user,
        "products": products,
        "cost_centers": cost_centers,
        "suppliers": suppliers,
        "categories": categories,
        "units": units,
        "origem_tipo": origem_tipo,
        "origem_id": origem_id,
        "justificativa_prefill": justificativa_prefill,
        "title": "Nova Solicitação de Compra"
    })

@router.post("/solicitacoes/new")
async def create_request_submit(
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)],
    centro_custo_id: int = Form(...),
    justificativa: str = Form(...),
    urgencia: str = Form(...),
    data_necessaria: Optional[str] = Form(None),
    products_ids: List[int] = Form(...),
    quantities: List[float] = Form(...),
    estimated_prices: List[float] = Form(...),
    fornecedores_sugeridos: List[str] = Form(...)
):
    try:
        dt_necessaria = None
        if data_necessaria:
            dt_necessaria = datetime.strptime(data_necessaria, "%Y-%m-%d")

        itens_in = []
        for i in range(len(products_ids)):
            sug_forn_id = None
            if i < len(fornecedores_sugeridos) and fornecedores_sugeridos[i] and fornecedores_sugeridos[i].strip():
                try:
                    sug_forn_id = int(fornecedores_sugeridos[i])
                except ValueError:
                    pass
            itens_in.append(PurchaseRequestItemCreate(
                product_id=products_ids[i],
                quantidade=quantities[i],
                valor_estimado=estimated_prices[i],
                fornecedor_sugerido_id=sug_forn_id
            ))

        request_in = PurchaseRequestCreate(
            centro_custo_id=centro_custo_id,
            justificativa=justificativa,
            urgencia=urgencia,
            data_necessaria=dt_necessaria,
            itens=itens_in
        )

        # Validate budget
        cc = await crud_proc.get_cost_center(db, cc_id=centro_custo_id)
        estimated_total = Decimal(str(sum(item.quantidade * item.valor_estimado for item in itens_in)))
        status_req = PurchaseRequestStatus.PENDENTE
        if cc and cc.bloquear_limite and (cc.orcamento_mensal_usado + estimated_total > cc.orcamento_mensal):
            status_req = PurchaseRequestStatus.AGUARDANDO_ORCAMENTO

        req = await crud_proc.create_purchase_request(
            db, request_in=request_in, solicitante_id=current_user.id, departamento_id=current_user.departamento_id or 1, status=status_req
        )
        
        # Log History
        await crud_proc.log_history(
            db, tabela="purchase_requests", registro_id=req.id, user_id=current_user.id, acao="Solicitação de Compra Criada"
        )

        # Notificar gestores sobre nova solicitação de compra
        try:
            from app.services.notification_service import notification_service
            total_est = float(sum(item.quantidade * item.valor_estimado for item in itens_in))
            await notification_service.notify_purchase_request(
                db=db,
                request_id=req.id,
                request_numero=req.numero,
                solicitante_nome=current_user.nome,
                urgencia=urgencia,
                total_estimado=total_est
            )
        except Exception as e:
            print(f"[NOTIFICATION][ERRO] notify_purchase_request: {e}")

        return RedirectResponse(url="/compras/solicitacoes", status_code=303)
    except Exception as e:
        logger.error(f"Erro ao criar solicitação de compra: {e}")
        products = await crud_proc.get_products(db, limit=500)
        cost_centers = await crud_proc.get_cost_centers(db, limit=100)
        suppliers = (await db.execute(select(Fornecedor))).scalars().all()
        return templates.TemplateResponse("procurement/request_form.html", {
            "request": request,
            "user": current_user,
            "products": products,
            "cost_centers": cost_centers,
            "suppliers": suppliers,
            "error": f"Erro: {str(e)}",
            "title": "Nova Solicitação de Compra"
        })

@router.get("/solicitacoes/{request_id}", response_class=HTMLResponse)
async def request_detail(
    request_id: int,
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    req_obj = await crud_proc.get_purchase_request(db, request_id)
    if not req_obj:
        return RedirectResponse(url="/compras/solicitacoes", status_code=303)
    
    # Calculate estimated total
    total = sum(item.quantidade * item.valor_estimado for item in req_obj.itens)
    
    # Get available approval levels
    # Fluxo: Solicitante -> Gestor -> Gerente -> Financeiro -> Diretoria -> Compras
    # Check current approvals status
    approvals = req_obj.approvals
    pending_level = None
    levels = ["Gestor", "Gerente", "Financeiro", "Diretoria", "Compras"]
    approved_levels = [app.nivel for app in approvals if app.status == "Aprovado"]
    
    for lvl in levels:
        if lvl not in approved_levels:
            pending_level = lvl
            break

    # Determine if current user can approve the pending level
    can_approve = False
    if pending_level and req_obj.status != PurchaseRequestStatus.AGUARDANDO_ORCAMENTO:
        role_lower = current_user.role.value.lower()
        if pending_level == "Gestor" and role_lower in ["admin", "gerente_ti", "gerente_infra", "comprador"]:
            can_approve = True
        elif pending_level == "Gerente" and role_lower in ["admin", "gerente_ti", "gerente_infra", "comprador"]:
            can_approve = True
        elif pending_level == "Financeiro" and role_lower in ["admin", "comprador"]: # or finance role
            can_approve = True
        elif pending_level == "Diretoria" and role_lower in ["admin", "comprador"]:
            can_approve = True
        elif pending_level == "Compras" and role_lower in ["admin", "comprador"]:
            can_approve = True

    return templates.TemplateResponse("procurement/request_detail.html", {
        "request": request,
        "user": current_user,
        "solicitacao": req_obj,
        "total_estimado": total,
        "pending_level": pending_level,
        "can_approve": can_approve,
        "title": f"Solicitação {req_obj.numero}"
    })

@router.post("/solicitacoes/{request_id}/decidir")
async def decide_request(
    request_id: int,
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)],
    nivel: str = Form(...),
    decisao: str = Form(...), # Aprovado or Reprovado
    observacao: Optional[str] = Form(None)
):
    req_obj = await crud_proc.get_purchase_request(db, request_id)
    if not req_obj:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada")

    # Check if the user is authorized to approve this level
    authorized = False
    role_lower = current_user.role.value.lower()
    if nivel == "Gestor" and role_lower in ["admin", "gerente_ti", "gerente_infra", "comprador"]:
        authorized = True
    elif nivel == "Gerente" and role_lower in ["admin", "gerente_ti", "gerente_infra", "comprador"]:
        authorized = True
    elif nivel == "Financeiro" and role_lower in ["admin", "comprador"]:
        authorized = True
    elif nivel == "Diretoria" and role_lower in ["admin", "comprador"]:
        authorized = True
    elif nivel == "Compras" and role_lower in ["admin", "comprador"]:
        authorized = True

    if not authorized:
        raise HTTPException(status_code=403, detail="Não autorizado a decidir este nível de solicitação")

    # Save Approval record
    app = PurchaseApproval(
        request_id=request_id,
        nivel=nivel,
        aprovador_id=current_user.id,
        status=decisao,
        observacao=observacao,
        data_decisao=now_sp()
    )
    db.add(app)
    
    # Update Request Status if rejected or if it was the final approval level
    if decisao == "Reprovado":
        req_obj.status = PurchaseRequestStatus.REPROVADA
    else:
        # If it was the final level (Compras), transition to Aprovada
        if nivel == "Compras":
            req_obj.status = PurchaseRequestStatus.APROVADA
            
            # Auto update Cost Center budget used
            cc = await crud_proc.get_cost_center(db, req_obj.centro_custo_id)
            if cc:
                estimated_total = Decimal(str(sum(float(item.quantidade) * float(item.valor_estimado) for item in req_obj.itens)))
                cc.orcamento_mensal_usado += estimated_total
                cc.orcamento_anual_usado += estimated_total
                db.add(cc)
        else:
            req_obj.status = PurchaseRequestStatus.EM_APROVACAO
            
    db.add(req_obj)
    await db.commit()
    
    await crud_proc.log_history(
        db, tabela="purchase_requests", registro_id=request_id, user_id=current_user.id, acao=f"Decisão de {nivel}: {decisao}"
    )

    return RedirectResponse(url=f"/compras/solicitacoes/{request_id}", status_code=303)


@router.post("/solicitacoes/{request_id}/liberar-orcamento")
async def release_budget(
    request_id: int,
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    if current_user.role.value.lower() not in ["admin", "gerente_ti", "gerente_infra"]:
        raise HTTPException(status_code=403, detail="Não autorizado a liberar orçamento")
        
    req_obj = await crud_proc.get_purchase_request(db, request_id)
    if not req_obj:
        raise HTTPException(status_code=404, detail="Solicitação não encontrada")
        
    req_obj.status = PurchaseRequestStatus.PENDENTE if not req_obj.approvals else PurchaseRequestStatus.EM_APROVACAO
    db.add(req_obj)
    await db.commit()
    
    await crud_proc.log_history(
        db, tabela="purchase_requests", registro_id=request_id, user_id=current_user.id, acao="Orçamento Liberado pelo Administrador"
    )
    return RedirectResponse(url=f"/compras/solicitacoes/{request_id}", status_code=303)


# -----------------
# QUOTATIONS & ORDERS
# -----------------
@router.get("/cotacoes", response_class=HTMLResponse)
async def list_quotations(
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    cotacoes = (await db.execute(select(PurchaseQuotation).options(selectinload(PurchaseQuotation.request)).order_by(desc(PurchaseQuotation.data_criacao)))).scalars().all()
    return templates.TemplateResponse("procurement/quotations_list.html", {
        "request": request,
        "user": current_user,
        "cotacoes": cotacoes,
        "title": "Cotações de Compra"
    })

@router.get("/cotacoes/new", response_class=HTMLResponse)
async def new_quotation_form(
    request_id: int,
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    req_obj = await crud_proc.get_purchase_request(db, request_id)
    suppliers = (await db.execute(select(Fornecedor))).scalars().all()
    return templates.TemplateResponse("procurement/quotation_form.html", {
        "request": request,
        "user": current_user,
        "solicitacao": req_obj,
        "suppliers": suppliers,
        "title": "Nova Cotação de Preços"
    })

@router.post("/cotacoes/new")
async def create_quotation_submit(
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)],
    request_id: int = Form(...),
    fornecedor_ids: List[int] = Form(...),
    fretes: List[float] = Form(...),
    prazos: List[int] = Form(...),
    garantias: List[int] = Form(...),
    formas_pagamento: List[str] = Form(...),
    observacoes: List[str] = Form(...),
    # Preços unitários dos itens indexados por fornecedor e produto
    # Formato dos campos: unit_price_{supplier_id}_{product_id}
):
    try:
        req_obj = await crud_proc.get_purchase_request(db, request_id)
        if not req_obj:
            raise HTTPException(status_code=404, detail="Solicitação não encontrada")

        form_data = await request.form()

        # Criar a cotação central
        year = now_sp().year
        prefix = f"CQ-{year}-"
        cq_count = len((await db.execute(select(PurchaseQuotation))).scalars().all()) + 1
        num = f"{prefix}{cq_count:06d}"

        cq = PurchaseQuotation(
            numero=num,
            request_id=request_id,
            status="Em cotação"
        )
        db.add(cq)
        await db.flush()

        for s_idx, f_id in enumerate(fornecedor_ids):
            # Calcular o valor total cotado por este fornecedor
            val_total_fornecedor = 0.00
            itens_cotados = []
            
            for item in req_obj.itens:
                field_name = f"unit_price_{f_id}_{item.product_id}"
                unit_val_str = form_data.get(field_name)
                unit_val = float(unit_val_str) if unit_val_str else 0.00
                val_total_fornecedor += (unit_val * float(item.quantidade))
                
                itens_cotados.append((item.product_id, item.quantidade, unit_val))

            val_total_fornecedor += fretes[s_idx]

            # Criar fornecedor participante
            cq_supplier = PurchaseQuotationSupplier(
                quotation_id=cq.id,
                fornecedor_id=f_id,
                valor_total=val_total_fornecedor,
                frete=fretes[s_idx],
                prazo_entrega_dias=prazos[s_idx],
                garantia_meses=garantias[s_idx],
                forma_pagamento=formas_pagamento[s_idx],
                observacoes=observacoes[s_idx]
            )
            db.add(cq_supplier)
            await db.flush()

            # Adicionar itens cotados
            for prod_id, qty, unit_price in itens_cotados:
                cq_item = PurchaseQuotationItem(
                    quotation_supplier_id=cq_supplier.id,
                    product_id=prod_id,
                    quantidade=qty,
                    valor_unitario=unit_price
                )
                db.add(cq_item)

        # Atualizar status da solicitação
        req_obj.status = PurchaseRequestStatus.CONVERTIDA_COTACAO
        db.add(req_obj)

        await db.commit()
        return RedirectResponse(url="/compras/cotacoes", status_code=303)
    except Exception as e:
        logger.error(f"Erro ao registrar cotação: {e}")
        return RedirectResponse(url=f"/compras/cotacoes/new?request_id={request_id}", status_code=303)

@router.get("/cotacoes/{quotation_id}", response_class=HTMLResponse)
async def quotation_compare(
    quotation_id: int,
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    compare_data = await serv_proc.calculate_quotation_comparison(quotation_id, db)
    if not compare_data:
        return RedirectResponse(url="/compras/cotacoes", status_code=303)

    return templates.TemplateResponse("procurement/quotation_compare.html", {
        "request": request,
        "user": current_user,
        **compare_data,
        "title": f"Comparativo {compare_data['quotation'].numero}"
    })

@router.post("/cotacoes/{quotation_id}/select-winner")
async def select_winning_supplier(
    quotation_id: int,
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)],
    winner_supplier_id: int = Form(...)
):
    # Obter o fornecedor cotado da cotação
    res = await db.execute(
        select(PurchaseQuotationSupplier)
        .options(selectinload(PurchaseQuotationSupplier.itens))
        .filter(and_(PurchaseQuotationSupplier.quotation_id == quotation_id, PurchaseQuotationSupplier.id == winner_supplier_id))
    )
    winner = res.scalars().first()
    if not winner:
        raise HTTPException(status_code=404, detail="Fornecedor cotado não encontrado")

    # Marcar vencedor
    winner.escolhido = True
    db.add(winner)

    # Obter cotação para finalizar
    cq_res = await db.execute(select(PurchaseQuotation).filter(PurchaseQuotation.id == quotation_id))
    cq = cq_res.scalars().first()
    cq.status = "Finalizada"
    db.add(cq)

    # Obter a solicitação de compra original para propagar o centro de custo
    req_res = await db.execute(select(PurchaseRequest).filter(PurchaseRequest.id == cq.request_id))
    req = req_res.scalars().first()
    centro_custo_id = req.centro_custo_id if req else 1

    # Gerar automaticamente o Pedido de Compra (PurchaseOrder)
    num = await crud_proc.generate_order_number(db)
    order = PurchaseOrder(
        numero=num,
        fornecedor_id=winner.fornecedor_id,
        centro_custo_id=centro_custo_id,
        request_id=cq.request_id,
        quotation_id=cq.id,
        valor_total=winner.valor_total,
        desconto=0.00,
        ipi=0.00,
        icms=0.00,
        frete=winner.frete,
        status=PurchaseOrderStatus.ABERTO
    )
    db.add(order)
    await db.flush()

    for item in winner.itens:
        db_item = PurchaseOrderItem(
            order_id=order.id,
            product_id=item.product_id,
            quantidade=item.quantidade,
            valor_unitario=item.valor_unitario,
            total_item=(item.quantidade * item.valor_unitario)
        )
        db.add(db_item)

    await db.commit()

    # Notificar gestores sobre o PO emitido
    try:
        from app.services.notification_service import notification_service
        fornecedor_res = await db.get(Fornecedor, winner.fornecedor_id)
        forn_nome = fornecedor_res.nome if fornecedor_res else f"Fornecedor #{winner.fornecedor_id}"
        await notification_service.notify_purchase_order(
            db=db,
            order_id=order.id,
            order_numero=order.numero,
            fornecedor_nome=forn_nome,
            valor_total=float(order.valor_total)
        )
    except Exception as e:
        print(f"[NOTIFICATION][ERRO] notify_purchase_order: {e}")

    return RedirectResponse(url="/compras/pedidos", status_code=303)


# ---------------
# PURCHASE ORDERS
# ---------------
@router.get("/pedidos", response_class=HTMLResponse)
async def list_orders(
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    pedidos = await crud_proc.get_purchase_orders(db, limit=100)
    return templates.TemplateResponse("procurement/orders_list.html", {
        "request": request,
        "user": current_user,
        "pedidos": pedidos,
        "title": "Pedidos de Compra"
    })

@router.get("/pedidos/{order_id}", response_class=HTMLResponse)
async def order_detail(
    order_id: int,
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    order = await crud_proc.get_purchase_order(db, order_id)
    if not order:
        return RedirectResponse(url="/compras/pedidos", status_code=303)
        
    return templates.TemplateResponse("procurement/order_detail.html", {
        "request": request,
        "user": current_user,
        "pedido": order,
        "title": f"Pedido {order.numero}"
    })


# ---------
# RECEIVING
# ---------
@router.get("/pedidos/{order_id}/receber", response_class=HTMLResponse)
async def receiving_form(
    order_id: int,
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    order = await crud_proc.get_purchase_order(db, order_id)
    if not order:
        return RedirectResponse(url="/compras/pedidos", status_code=303)

    # Buscar notas fiscais desse fornecedor
    notas_res = await db.execute(
        select(NotaFiscal).filter(NotaFiscal.fornecedor_id == order.fornecedor_id)
    )
    notas = notas_res.scalars().all()

    # Verificar se há equipamentos no pedido
    has_equipment = any(item.product.tipo == ProductType.EQUIPAMENTO for item in order.itens)
    armazenamentos = []
    locais = []
    
    if has_equipment:
        from app.models.location import Armazenamento, Localizacao
        
        # Buscar armazenamentos
        arm_res = await db.execute(select(Armazenamento))
        armazenamentos = arm_res.scalars().all()
        
        # Se não houver nenhum, criar um padrão
        if not armazenamentos:
            default_arm = Armazenamento(nome="Almoxarifado TI (Compras)", capacidade_max=1000, tipo_itens="Equipamentos")
            db.add(default_arm)
            await db.commit()
            arm_res = await db.execute(select(Armazenamento))
            armazenamentos = arm_res.scalars().all()
            
        # Buscar localizações
        loc_res = await db.execute(select(Localizacao))
        locais = loc_res.scalars().all()

    return templates.TemplateResponse("procurement/receiving_form.html", {
        "request": request,
        "user": current_user,
        "pedido": order,
        "notas": notas,
        "has_equipment": has_equipment,
        "armazenamentos": armazenamentos,
        "locais": locais,
        "title": f"Receber Pedido {order.numero}"
    })


@router.post("/pedidos/{order_id}/receber")
async def create_receiving_submit(
    order_id: int,
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)],
    nota_fiscal_id: Optional[int] = Form(None),
    observacoes: Optional[str] = Form(None),
    product_ids: List[int] = Form(...),
    quantities_received: List[float] = Form(...),
    divergencias: List[Optional[str]] = Form(...),
    current_local_id: Optional[int] = Form(None),
    current_armazenamento_id: Optional[int] = Form(None)
):
    try:
        itens_in = []
        for i in range(len(product_ids)):
            itens_in.append(PurchaseReceivingItemCreate(
                product_id=product_ids[i],
                quantidade_recebida=quantities_received[i],
                divergencias=divergencias[i] if (i < len(divergencias) and divergencias[i]) else None
            ))

        receiving_in = PurchaseReceivingCreate(
            order_id=order_id,
            nota_fiscal_id=nota_fiscal_id,
            observacoes=observacoes,
            itens=itens_in
        )

        rec = await crud_proc.create_receiving(db, receiving_in=receiving_in, responsavel_id=current_user.id)
        
        # Trigger Asset Creation & Stock Addition
        created_assets = await serv_proc.convert_receiving_to_assets(
            rec.id, 
            db, 
            current_user.id,
            current_local_id=current_local_id,
            current_armazenamento_id=current_armazenamento_id
        )
 
        # Update Order Status to fully received
        order = await crud_proc.get_purchase_order(db, order_id)
        order.status = PurchaseOrderStatus.RECEBIDO_TOTAL
        db.add(order)
        await db.commit()

        # Verificar itens de consumo com estoque baixo após recebimento
        try:
            from app.services.notification_service import notification_service
            from app.models.procurement import ProductType
            for item_rec in rec.itens:
                if item_rec.product and item_rec.product.tipo == ProductType.CONSUMIVEL:
                    stock_res = await db.execute(
                        select(MaterialStock).filter(MaterialStock.product_id == item_rec.product_id)
                    )
                    stock = stock_res.scalars().first()
                    if stock and stock.quantidade_saldo < 5:
                        await notification_service.notify_low_stock(
                            db=db,
                            product_name=item_rec.product.nome,
                            saldo_atual=float(stock.quantidade_saldo),
                            unidade=item_rec.product.unidade_medida or "un"
                        )
        except Exception as e:
            print(f"[NOTIFICATION][ERRO] notify_low_stock após recebimento: {e}")

        if created_assets:
            return RedirectResponse(url=f"/compras/pedidos/{order_id}/recebido-sucesso/{rec.id}", status_code=303)
 
        return RedirectResponse(url="/compras/pedidos", status_code=303)
    except Exception as e:
        logger.error(f"Erro ao registrar recebimento: {e}")
        return RedirectResponse(url=f"/compras/pedidos/{order_id}/receber", status_code=303)
 
 
@router.get("/pedidos/{order_id}/recebido-sucesso/{receiving_id}", response_class=HTMLResponse)
async def receiving_success(
    order_id: int,
    receiving_id: int,
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    from app.models.asset import Asset
    
    # Buscar recebimento
    res = await db.execute(
        select(PurchaseReceiving)
        .options(
            selectinload(PurchaseReceiving.itens),
            selectinload(PurchaseReceiving.order)
        )
        .filter(PurchaseReceiving.id == receiving_id)
    )
    receiving = res.scalars().first()
    if not receiving:
        return RedirectResponse(url="/compras/pedidos", status_code=303)
        
    # Buscar ativos criados
    asset_ids = [item.ativo_criado_id for item in receiving.itens if item.ativo_criado_id]
    assets = []
    if asset_ids:
        assets_res = await db.execute(
            select(Asset)
            .options(
                selectinload(Asset.current_local),
                selectinload(Asset.current_armazenamento)
            )
            .filter(Asset.id.in_(asset_ids))
        )
        assets = assets_res.scalars().all()
        
    return templates.TemplateResponse("procurement/receiving_success.html", {
        "request": request,
        "user": current_user,
        "pedido": receiving.order,
        "assets": assets,
        "title": "Recebimento com Sucesso!"
    })


# -----
# STOCK
# -----
@router.get("/estoque", response_class=HTMLResponse)
async def list_stock(
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    stocks = (await db.execute(
        select(MaterialStock)
        .options(selectinload(MaterialStock.product).selectinload(PurchaseProduct.categoria))
    )).scalars().all()

    return templates.TemplateResponse("procurement/stock_list.html", {
        "request": request,
        "user": current_user,
        "estoques": stocks,
        "title": "Almoxarifado de Consumo"
    })


# --------------------
# AUXILIARY REGISTERS (PRODUCTS & COST CENTERS)
# --------------------

@router.get("/produtos", response_class=HTMLResponse)
async def list_products(
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    produtos = await crud_proc.get_products(db, limit=1000)
    return templates.TemplateResponse("procurement/products_list.html", {
        "request": request,
        "user": current_user,
        "produtos": produtos,
        "title": "Produtos para Compra"
    })


@router.get("/produtos/new", response_class=HTMLResponse)
async def new_product_form(
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    if current_user.role not in [UserRole.ADMIN, UserRole.GERENTE, UserRole.GERENTE_INFRA, UserRole.COMPRADOR]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    categories = await crud_proc.get_categories(db, limit=100)
    units = await crud_proc.get_units(db)
    
    # If no units exist, create some defaults
    if not units:
        defaults = [("UN", "Unidade"), ("CX", "Caixa"), ("PC", "Pacote"), ("MT", "Metros"), ("JG", "Jogo"), ("SV", "Serviço")]
        for s, d in defaults:
            await crud_proc.create_unit(db, s, d)
        units = await crud_proc.get_units(db)

    return templates.TemplateResponse("procurement/product_form.html", {
        "request": request,
        "user": current_user,
        "categories": categories,
        "units": units,
        "title": "Novo Produto"
    })

# --- AJAX Endpoints for Dynamic Creation ---

@router.post("/api/categorias")
async def api_create_category(
    nome: str = Form(...),
    descricao: Optional[str] = Form(None),
    current_user: User = Depends(get_active_user_web),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role not in [UserRole.ADMIN, UserRole.GERENTE, UserRole.GERENTE_INFRA, UserRole.COMPRADOR]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    cat_in = PurchaseCategoryCreate(nome=nome, descricao=descricao)
    try:
        new_cat = await crud_proc.create_category(db, cat_in)
        return {"success": True, "id": new_cat.id, "nome": new_cat.nome}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/api/unidades")
async def api_create_unit(
    sigla: str = Form(...),
    descricao: Optional[str] = Form(None),
    current_user: User = Depends(get_active_user_web),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role not in [UserRole.ADMIN, UserRole.GERENTE, UserRole.GERENTE_INFRA, UserRole.COMPRADOR]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    try:
        new_unit = await crud_proc.create_unit(db, sigla=sigla, descricao=descricao)
        return {"success": True, "sigla": new_unit.sigla, "descricao": new_unit.descricao}
    except Exception as e:
        return {"success": False, "error": str(e)}

@router.post("/api/produtos")
async def api_create_product(
    codigo: str = Form(...),
    nome: str = Form(...),
    categoria_id: int = Form(...),
    unidade: str = Form(...),
    tipo: str = Form(...),
    marca: Optional[str] = Form(None),
    modelo: Optional[str] = Form(None),
    fabricante: Optional[str] = Form(None),
    descricao: Optional[str] = Form(None),
    current_user: User = Depends(get_active_user_web),
    db: AsyncSession = Depends(get_db)
):
    if current_user.role not in [UserRole.ADMIN, UserRole.GERENTE, UserRole.GERENTE_INFRA, UserRole.COMPRADOR]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    try:
        existing = await crud_proc.get_product_by_codigo(db, codigo)
        if existing:
            return {"success": False, "error": "Já existe um produto com este código."}
            
        product_in = PurchaseProductCreate(
            codigo=codigo,
            nome=nome,
            categoria_id=categoria_id,
            unidade=unidade,
            tipo=ProductType(tipo),
            marca=marca,
            modelo=modelo,
            fabricante=fabricante,
            descricao=descricao,
            ativo=True
        )
        new_prod = await crud_proc.create_product(db, product_in)
        return {"success": True, "id": new_prod.id, "nome": new_prod.nome, "unidade": new_prod.unidade}
    except Exception as e:
        return {"success": False, "error": str(e)}



@router.post("/produtos/new")
async def create_product_submit(
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)],
    codigo: str = Form(...),
    nome: str = Form(...),
    categoria_id: int = Form(...),
    unidade: str = Form(...),
    tipo: str = Form(...),
    marca: Optional[str] = Form(None),
    modelo: Optional[str] = Form(None),
    fabricante: Optional[str] = Form(None),
    descricao: Optional[str] = Form(None)
):
    if current_user.role not in [UserRole.ADMIN, UserRole.GERENTE, UserRole.GERENTE_INFRA, UserRole.COMPRADOR]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    try:
        existing = await crud_proc.get_product_by_codigo(db, codigo)
        if existing:
            raise ValueError("Já existe um produto cadastrado com este código!")
            
        product_in = PurchaseProductCreate(
            codigo=codigo,
            nome=nome,
            categoria_id=categoria_id,
            unidade=unidade,
            tipo=ProductType(tipo),
            marca=marca,
            modelo=modelo,
            fabricante=fabricante,
            descricao=descricao,
            ativo=True
        )
        await crud_proc.create_product(db, product_in)
        return RedirectResponse(url="/compras/produtos", status_code=303)
    except Exception as e:
        logger.error(f"Erro ao criar produto: {e}")
        categories = await crud_proc.get_categories(db, limit=100)
        return templates.TemplateResponse("procurement/product_form.html", {
            "request": request,
            "user": current_user,
            "categories": categories,
            "error": str(e),
            "title": "Novo Produto"
        })


@router.get("/produtos/{product_id}/edit", response_class=HTMLResponse)
async def edit_product_form(
    product_id: int,
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    if current_user.role not in [UserRole.ADMIN, UserRole.GERENTE, UserRole.GERENTE_INFRA, UserRole.COMPRADOR]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    produto = await crud_proc.get_product(db, product_id)
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
    categories = await crud_proc.get_categories(db, limit=100)
    units = await crud_proc.get_units(db)
    return templates.TemplateResponse("procurement/product_form.html", {
        "request": request,
        "user": current_user,
        "categories": categories,
        "units": units,
        "produto": produto,
        "title": f"Editar Produto: {produto.nome}"
    })


@router.post("/produtos/{product_id}/edit", response_class=HTMLResponse)
async def edit_product_submit(
    product_id: int,
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)],
    codigo: str = Form(...),
    nome: str = Form(...),
    categoria_id: int = Form(...),
    unidade: str = Form(...),
    tipo: str = Form(...),
    marca: Optional[str] = Form(None),
    modelo: Optional[str] = Form(None),
    fabricante: Optional[str] = Form(None),
    descricao: Optional[str] = Form(None),
    ativo: Optional[str] = Form(None)
):
    if current_user.role not in [UserRole.ADMIN, UserRole.GERENTE, UserRole.GERENTE_INFRA, UserRole.COMPRADOR]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    produto = await crud_proc.get_product(db, product_id)
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não encontrado")
        
    try:
        # Check if code is already used by ANOTHER product
        existing = await crud_proc.get_product_by_codigo(db, codigo)
        if existing and existing.id != product_id:
            raise ValueError("Já existe outro produto cadastrado com este código!")
            
        is_active = True
        if ativo is not None:
            is_active = ativo.lower() in ("true", "1", "yes", "on")
        else:
            is_active = False # HTML unchecked checkbox returns nothing
            
        product_in = PurchaseProductUpdate(
            codigo=codigo,
            nome=nome,
            categoria_id=categoria_id,
            unidade=unidade,
            tipo=ProductType(tipo),
            marca=marca,
            modelo=modelo,
            fabricante=fabricante,
            descricao=descricao,
            ativo=is_active
        )
        await crud_proc.update_product(db, db_prod=produto, product=product_in)
        return RedirectResponse(url="/compras/produtos", status_code=303)
    except Exception as e:
        logger.error(f"Erro ao editar produto: {e}")
        categories = await crud_proc.get_categories(db, limit=100)
        units = await crud_proc.get_units(db)
        return templates.TemplateResponse("procurement/product_form.html", {
            "request": request,
            "user": current_user,
            "categories": categories,
            "units": units,
            "produto": produto,
            "error": str(e),
            "title": f"Editar Produto: {produto.nome}"
        })



@router.get("/centro-custos", response_class=HTMLResponse)
async def list_cost_centers(
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    cost_centers = await crud_proc.get_cost_centers(db, limit=100)
    return templates.TemplateResponse("procurement/cost_centers_list.html", {
        "request": request,
        "user": current_user,
        "cost_centers": cost_centers,
        "title": "Centros de Custo"
    })


@router.get("/centro-custos/new", response_class=HTMLResponse)
async def new_cost_center_form(
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    if current_user.role not in [UserRole.ADMIN, UserRole.GERENTE, UserRole.GERENTE_INFRA]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    from app.models.location import Departamento
    departments = (await db.execute(select(Departamento))).scalars().all()
    users_list = (await db.execute(select(User).filter(User.is_active == True))).scalars().all()
    
    return templates.TemplateResponse("procurement/cost_center_form.html", {
        "request": request,
        "user": current_user,
        "departments": departments,
        "users_list": users_list,
        "title": "Novo Centro de Custo"
    })


@router.post("/centro-custos/new")
async def create_cost_center_submit(
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)],
    codigo: str = Form(...),
    nome: str = Form(...),
    departamento_id: Optional[int] = Form(None),
    responsavel_id: Optional[int] = Form(None),
    orcamento_mensal: float = Form(...),
    orcamento_anual: float = Form(...),
    alerta_limite: Optional[str] = Form(None),
    bloquear_limite: Optional[str] = Form(None)
):
    if current_user.role not in [UserRole.ADMIN, UserRole.GERENTE, UserRole.GERENTE_INFRA]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    try:
        existing = (await db.execute(select(CostCenter).filter(CostCenter.codigo == codigo))).scalars().first()
        if existing:
            raise ValueError("Já existe um centro de custo com este código!")
            
        cc_in = CostCenterCreate(
            codigo=codigo,
            nome=nome,
            departamento_id=departamento_id,
            responsavel_id=responsavel_id,
            orcamento_mensal=orcamento_mensal,
            orcamento_anual=orcamento_anual,
            alerta_limite=True if alerta_limite else False,
            bloquear_limite=True if bloquear_limite else False
        )
        
        db_cc = CostCenter(
            codigo=cc_in.codigo,
            nome=cc_in.nome,
            departamento_id=cc_in.departamento_id,
            responsavel_id=cc_in.responsavel_id,
            orcamento_mensal=cc_in.orcamento_mensal,
            orcamento_anual=cc_in.orcamento_anual,
            alerta_limite=cc_in.alerta_limite,
            bloquear_limite=cc_in.bloquear_limite,
            orcamento_mensal_usado=0.0,
            orcamento_anual_usado=0.0
        )
        db.add(db_cc)
        await db.commit()
        
        return RedirectResponse(url="/compras/centro-custos", status_code=303)
    except Exception as e:
        logger.error(f"Erro ao criar centro de custo: {e}")
        from app.models.location import Departamento
        departments = (await db.execute(select(Departamento))).scalars().all()
        users_list = (await db.execute(select(User).filter(User.is_active == True))).scalars().all()
        return templates.TemplateResponse("procurement/cost_center_form.html", {
            "request": request,
            "user": current_user,
            "departments": departments,
            "users_list": users_list,
            "error": str(e),
            "title": "Novo Centro de Custo"
        })


@router.get("/centro-custos/{cc_id}/edit", response_class=HTMLResponse)
async def edit_cost_center_form(
    cc_id: int,
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    if current_user.role not in [UserRole.ADMIN, UserRole.GERENTE, UserRole.GERENTE_INFRA]:
        raise HTTPException(status_code=403, detail="Não autorizado")
    
    cc = await crud_proc.get_cost_center(db, cc_id=cc_id)
    if not cc:
        raise HTTPException(status_code=404, detail="Centro de Custo não encontrado")
        
    from app.models.location import Departamento
    departments = (await db.execute(select(Departamento))).scalars().all()
    users_list = (await db.execute(select(User).filter(User.is_active == True))).scalars().all()
    
    return templates.TemplateResponse("procurement/cost_center_form.html", {
        "request": request,
        "user": current_user,
        "cc": cc,
        "departments": departments,
        "users_list": users_list,
        "title": f"Editar Centro de Custo: {cc.nome}"
    })


@router.post("/centro-custos/{cc_id}/edit")
async def edit_cost_center_submit(
    cc_id: int,
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)],
    nome: str = Form(...),
    departamento_id: Optional[int] = Form(None),
    responsavel_id: Optional[int] = Form(None),
    orcamento_mensal: float = Form(...),
    orcamento_anual: float = Form(...),
    alerta_limite: Optional[str] = Form(None),
    bloquear_limite: Optional[str] = Form(None)
):
    if current_user.role not in [UserRole.ADMIN, UserRole.GERENTE, UserRole.GERENTE_INFRA]:
        raise HTTPException(status_code=403, detail="Não autorizado")
        
    cc = await crud_proc.get_cost_center(db, cc_id=cc_id)
    if not cc:
        raise HTTPException(status_code=404, detail="Centro de Custo não encontrado")
        
    try:
        cc.nome = nome
        cc.departamento_id = departamento_id
        cc.responsavel_id = responsavel_id
        cc.orcamento_mensal = orcamento_mensal
        cc.orcamento_anual = orcamento_anual
        cc.alerta_limite = True if alerta_limite else False
        cc.bloquear_limite = True if bloquear_limite else False
        
        db.add(cc)
        await db.commit()
        return RedirectResponse(url="/compras/centro-custos", status_code=303)
    except Exception as e:
        logger.error(f"Erro ao editar centro de custo: {e}")
        from app.models.location import Departamento
        departments = (await db.execute(select(Departamento))).scalars().all()
        users_list = (await db.execute(select(User).filter(User.is_active == True))).scalars().all()
        return templates.TemplateResponse("procurement/cost_center_form.html", {
            "request": request,
            "user": current_user,
            "cc": cc,
            "departments": departments,
            "users_list": users_list,
            "error": str(e),
            "title": f"Editar Centro de Custo: {cc.nome}"
        })


@router.post("/centro-custos/{cc_id}/delete")
async def delete_cost_center(
    cc_id: int,
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    if current_user.role not in [UserRole.ADMIN, UserRole.GERENTE, UserRole.GERENTE_INFRA]:
        raise HTTPException(status_code=403, detail="Não autorizado")
        
    cc = await crud_proc.get_cost_center(db, cc_id=cc_id)
    if not cc:
        raise HTTPException(status_code=404, detail="Centro de Custo não encontrado")
        
    try:
        from app.models.procurement import PurchaseRequest
        existing_requests = (await db.execute(select(PurchaseRequest).filter(PurchaseRequest.centro_custo_id == cc_id))).scalars().first()
        if existing_requests:
            raise ValueError("Não é possível excluir este Centro de Custo pois existem solicitações de compra vinculadas a ele.")
            
        await db.delete(cc)
        await db.commit()
        return RedirectResponse(url="/compras/centro-custos", status_code=303)
    except Exception as e:
        logger.error(f"Erro ao excluir centro de custo: {e}")
        await db.rollback()
        cost_centers = await crud_proc.get_cost_centers(db, limit=100)
        return templates.TemplateResponse("procurement/cost_centers_list.html", {
            "request": request,
            "user": current_user,
            "cost_centers": cost_centers,
            "error": str(e),
            "title": "Centros de Custo"
        })


# --------------------
# CONTRACTS LIFECYCLE MANAGEMENT
# --------------------

@router.get("/contratos", response_class=HTMLResponse)
async def list_contracts(
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    contracts = await crud_proc.get_contracts(db, limit=100)
    contracts_data = []
    for c in contracts:
        dias = (c.data_fim - now_sp()).days
        tag_color = "bg-gray-100 text-gray-800 border-gray-300"
        tag_text = f"{dias} dias"
        if dias < 0:
            tag_color = "bg-red-200 text-red-900 border-red-500 font-extrabold"
            tag_text = "Expirado"
        elif dias <= 7:
            tag_color = "bg-red-100 text-red-800 border-red-400 font-bold"
            tag_text = "Crítico (7d)"
        elif dias <= 15:
            tag_color = "bg-orange-100 text-orange-800 border-orange-400 font-bold"
            tag_text = "Alerta (15d)"
        elif dias <= 30:
            tag_color = "bg-amber-100 text-amber-800 border-amber-400"
            tag_text = "Atenção (30d)"
        elif dias <= 60:
            tag_color = "bg-blue-100 text-blue-800 border-blue-400"
            tag_text = "60 dias"
        elif dias <= 90:
            tag_color = "bg-green-100 text-green-800 border-green-400"
            tag_text = "90 dias"
            
        contracts_data.append({
            "contract": c,
            "dias": dias,
            "tag_color": tag_color,
            "tag_text": tag_text
        })
        
    return templates.TemplateResponse("procurement/contracts_list.html", {
        "request": request,
        "user": current_user,
        "contratos_data": contracts_data,
        "title": "Contratos de TI"
    })


@router.get("/contratos/new", response_class=HTMLResponse)
async def new_contract_form(
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    suppliers = (await db.execute(select(Fornecedor))).scalars().all()
    return templates.TemplateResponse("procurement/contract_form.html", {
        "request": request,
        "user": current_user,
        "suppliers": suppliers,
        "title": "Novo Contrato"
    })


import os
import shutil

@router.post("/contratos/new")
async def create_contract_submit(
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)],
    numero: str = Form(...),
    fornecedor_id: int = Form(...),
    tipo: str = Form(...),
    periodicidade: str = Form(...),
    data_inicio: str = Form(...),
    data_fim: str = Form(...),
    valor: float = Form(...),
    renovacao_automatica: Optional[str] = Form(None),
    pdf_file: UploadFile = File(None)
):
    try:
        existing = (await db.execute(select(PurchaseContract).filter(PurchaseContract.numero == numero))).scalars().first()
        if existing:
            raise ValueError("Já existe um contrato cadastrado com este número!")
            
        dt_ini = datetime.strptime(data_inicio, "%Y-%m-%d")
        dt_fim = datetime.strptime(data_fim, "%Y-%m-%d")
        
        pdf_path = None
        if pdf_file and pdf_file.filename:
            os.makedirs("static/uploads", exist_ok=True)
            filename = f"contrato_{numero.replace('/', '_')}_{pdf_file.filename}"
            save_path = os.path.join("static/uploads", filename)
            with open(save_path, "wb") as f:
                shutil.copyfileobj(pdf_file.file, f)
            pdf_path = filename
            
        contract_in = PurchaseContractCreate(
            fornecedor_id=fornecedor_id,
            tipo=tipo,
            numero=numero,
            data_inicio=dt_ini,
            data_fim=dt_fim,
            renovacao_automatica=True if renovacao_automatica else False,
            valor=valor,
            periodicidade=periodicidade,
            arquivo_pdf_path=pdf_path
        )
        
        await crud_proc.create_contract(db, contract_in)
        return RedirectResponse(url="/compras/contratos", status_code=303)
    except Exception as e:
        logger.error(f"Erro ao cadastrar contrato: {e}")
        suppliers = (await db.execute(select(Fornecedor))).scalars().all()
        return templates.TemplateResponse("procurement/contract_form.html", {
            "request": request,
            "user": current_user,
            "suppliers": suppliers,
            "error": str(e),
            "title": "Novo Contrato"
        })


@router.get("/contratos/{contract_id}", response_class=HTMLResponse)
async def contract_detail(
    contract_id: int,
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    contrato = await crud_proc.get_contract(db, contract_id)
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato não encontrado")
        
    dias = (contrato.data_fim - now_sp()).days
    tag_color = "bg-gray-100 text-gray-800 border-gray-300"
    tag_text = f"{dias} dias"
    if dias < 0:
        tag_color = "bg-red-200 text-red-900 border-red-500 font-extrabold"
        tag_text = "Expirado"
    elif dias <= 7:
        tag_color = "bg-red-100 text-red-800 border-red-400 font-bold"
        tag_text = "Crítico (7d)"
    elif dias <= 15:
        tag_color = "bg-orange-100 text-orange-800 border-orange-400 font-bold"
        tag_text = "Alerta (15d)"
    elif dias <= 30:
        tag_color = "bg-amber-100 text-amber-800 border-amber-400"
        tag_text = "Atenção (30d)"
    elif dias <= 60:
        tag_color = "bg-blue-100 text-blue-800 border-blue-400"
        tag_text = "60 dias"
    elif dias <= 90:
        tag_color = "bg-green-100 text-green-800 border-green-400"
        tag_text = "90 dias"
        
    return templates.TemplateResponse("procurement/contract_detail.html", {
        "request": request,
        "user": current_user,
        "contrato": contrato,
        "dias": dias,
        "tag_color": tag_color,
        "tag_text": tag_text,
        "title": f"Contrato {contrato.numero}"
    })


@router.get("/contratos/{contract_id}/edit", response_class=HTMLResponse)
async def edit_contract_form(
    contract_id: int,
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    if current_user.role not in [UserRole.ADMIN, UserRole.GERENTE, UserRole.GERENTE_INFRA, UserRole.COMPRADOR]:
        raise HTTPException(status_code=403, detail="Não autorizado")
        
    contrato = await crud_proc.get_contract(db, contract_id)
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato não encontrado")
        
    suppliers = (await db.execute(select(Fornecedor))).scalars().all()
    return templates.TemplateResponse("procurement/contract_form.html", {
        "request": request,
        "user": current_user,
        "contrato": contrato,
        "suppliers": suppliers,
        "title": f"Editar Contrato {contrato.numero}"
    })


@router.post("/contratos/{contract_id}/edit")
async def edit_contract_submit(
    contract_id: int,
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)],
    numero: str = Form(...),
    fornecedor_id: int = Form(...),
    tipo: str = Form(...),
    periodicidade: str = Form(...),
    data_inicio: str = Form(...),
    data_fim: str = Form(...),
    valor: float = Form(...),
    renovacao_automatica: Optional[str] = Form(None),
    pdf_file: UploadFile = File(None)
):
    if current_user.role not in [UserRole.ADMIN, UserRole.GERENTE, UserRole.GERENTE_INFRA, UserRole.COMPRADOR]:
        raise HTTPException(status_code=403, detail="Não autorizado")
        
    contrato = await crud_proc.get_contract(db, contract_id)
    if not contrato:
        raise HTTPException(status_code=404, detail="Contrato não encontrado")
        
    try:
        existing = (await db.execute(select(PurchaseContract).filter(PurchaseContract.numero == numero))).scalars().first()
        if existing and existing.id != contract_id:
            raise ValueError("Já existe outro contrato cadastrado com este número!")
            
        dt_ini = datetime.strptime(data_inicio, "%Y-%m-%d")
        dt_fim = datetime.strptime(data_fim, "%Y-%m-%d")
        
        pdf_path = contrato.arquivo_pdf_path
        if pdf_file and pdf_file.filename:
            os.makedirs("static/uploads", exist_ok=True)
            filename = f"contrato_{numero.replace('/', '_')}_{pdf_file.filename}"
            save_path = os.path.join("static/uploads", filename)
            with open(save_path, "wb") as f:
                shutil.copyfileobj(pdf_file.file, f)
            pdf_path = filename
            
        contract_in = PurchaseContractUpdate(
            fornecedor_id=fornecedor_id,
            tipo=tipo,
            numero=numero,
            data_inicio=dt_ini,
            data_fim=dt_fim,
            renovacao_automatica=True if renovacao_automatica else False,
            valor=valor,
            periodicidade=periodicidade,
            arquivo_pdf_path=pdf_path
        )
        
        await crud_proc.update_contract(db, db_contract=contrato, contract=contract_in)
        return RedirectResponse(url=f"/compras/contratos/{contract_id}", status_code=303)
    except Exception as e:
        logger.error(f"Erro ao editar contrato: {e}")
        suppliers = (await db.execute(select(Fornecedor))).scalars().all()
        return templates.TemplateResponse("procurement/contract_form.html", {
            "request": request,
            "user": current_user,
            "contrato": contrato,
            "suppliers": suppliers,
            "error": str(e),
            "title": f"Editar Contrato {contrato.numero}"
        })


@router.post("/contratos/{contract_id}/delete")
async def delete_contract_submit(
    contract_id: int,
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    if current_user.role not in [UserRole.ADMIN, UserRole.GERENTE, UserRole.GERENTE_INFRA, UserRole.COMPRADOR]:
        raise HTTPException(status_code=403, detail="Não autorizado")
        
    success = await crud_proc.delete_contract(db, contract_id)
    if not success:
        raise HTTPException(status_code=404, detail="Contrato não encontrado")
        
    return RedirectResponse(url="/compras/contratos", status_code=303)



@router.get("/relatorios", response_class=HTMLResponse)
async def procurement_reports(
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    # Spent by Cost Center
    cc_res = await db.execute(select(CostCenter))
    cost_centers = cc_res.scalars().all()
    cc_spent_data = []
    for cc in cost_centers:
        used = float(cc.orcamento_mensal_usado) if cc.orcamento_mensal_usado else 0.0
        limit = float(cc.orcamento_mensal) if cc.orcamento_mensal else 0.0
        perc = (used / limit * 100) if limit > 0 else 0
        cc_spent_data.append({
            "nome": cc.nome,
            "codigo": cc.codigo,
            "usado": used,
            "limite": limit,
            "disponivel": max(0.0, limit - used),
            "porcentagem": min(100.0, perc)
        })

    # Category spent distribution
    category_spent = []
    res_cat = await db.execute(
        select(
            PurchaseCategory.nome,
            func.sum(PurchaseRequestItem.valor_estimado * PurchaseRequestItem.quantidade)
        )
        .join(PurchaseProduct, PurchaseRequestItem.product_id == PurchaseProduct.id)
        .join(PurchaseCategory, PurchaseProduct.categoria_id == PurchaseCategory.id)
        .join(PurchaseRequest, PurchaseRequestItem.request_id == PurchaseRequest.id)
        .filter(PurchaseRequest.status.in_([
            PurchaseRequestStatus.APROVADA, 
            PurchaseRequestStatus.CONVERTIDA_COTACAO
        ]))
        .group_by(PurchaseCategory.nome)
    )
    for row in res_cat.all():
        category_spent.append({
            "name": row[0],
            "total": float(row[1]) if row[1] else 0.0
        })

    # Contracts summary
    contracts_res = await db.execute(select(PurchaseContract))
    all_contracts = contracts_res.scalars().all()
    total_val_contracts = float(sum(c.valor for c in all_contracts))
    expired_cnt = 0
    expiring_30_cnt = 0
    for c in all_contracts:
        dias = (c.data_fim - now_sp()).days
        if dias < 0:
            expired_cnt += 1
        elif dias <= 30:
            expiring_30_cnt += 1

    contract_summary = {
        "total_valor": total_val_contracts,
        "total_count": len(all_contracts),
        "expired": expired_cnt,
        "expiring_30": expiring_30_cnt
    }

    return templates.TemplateResponse("procurement/reports.html", {
        "request": request,
        "user": current_user,
        "cc_data": cc_spent_data,
        "category_spent": category_spent,
        "contract_summary": contract_summary,
        "title": "Relatórios de Compras"
    })


@router.get("/relatorios/exportar")
async def export_procurement_csv(
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)],
    tipo: Optional[str] = "solicitacoes",
    status_filter: Optional[str] = None,
):
    """Exporta dados do módulo de Compras em CSV."""
    import io, csv
    from fastapi.responses import StreamingResponse

    output = io.StringIO()
    writer = csv.writer(output)

    if tipo == "contratos":
        writer.writerow(["Número", "Fornecedor", "Objeto", "Valor (R$)", "Início", "Fim", "Status", "Renovação Automática"])
        res = await db.execute(select(PurchaseContract).options(selectinload(PurchaseContract.fornecedor)))
        contratos = res.scalars().all()
        for c in contratos:
            status_calc = "Ativo" if c.data_fim and c.data_fim >= now_sp() else "Vencido"
            writer.writerow([
                c.numero,
                c.fornecedor.nome if c.fornecedor else "",
                c.tipo,
                float(c.valor),
                c.data_inicio.strftime("%d/%m/%Y") if c.data_inicio else "",
                c.data_fim.strftime("%d/%m/%Y") if c.data_fim else "",
                status_calc,
                "Sim" if c.renovacao_automatica else "Não"
            ])
        filename = "contratos_export.csv"
    else:
        # Default: solicitações
        writer.writerow(["Número", "Solicitante", "Centro de Custo", "Justificativa", "Urgência", "Status", "Data Criação", "Valor Estimado (R$)"])
        query = select(PurchaseRequest).options(
            selectinload(PurchaseRequest.solicitante),
            selectinload(PurchaseRequest.centro_custo),
            selectinload(PurchaseRequest.itens)
        ).order_by(desc(PurchaseRequest.data_criacao))
        if status_filter:
            query = query.filter(PurchaseRequest.status == status_filter)
        res = await db.execute(query)
        solicitacoes = res.scalars().all()
        for s in solicitacoes:
            total_val = sum(float(i.valor_estimado) * float(i.quantidade) for i in s.itens)
            writer.writerow([
                s.numero,
                s.solicitante.nome if s.solicitante else "",
                s.centro_custo.nome if s.centro_custo else "",
                s.justificativa,
                s.urgencia,
                s.status.value if hasattr(s.status, 'value') else str(s.status),
                s.data_criacao.strftime("%d/%m/%Y %H:%M") if s.data_criacao else "",
                f"{total_val:.2f}"
            ])
        filename = "solicitacoes_compras_export.csv"

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# --------------------
# PESQUISAS DE COMPRA (COTAÇÃO PRÉVIA)
# --------------------
@router.get("/pesquisas", response_class=HTMLResponse)
async def list_researches(
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    researches = await crud_proc.get_purchase_researches(db)
    return templates.TemplateResponse(
        "procurement/researches_list.html",
        {"request": request, "researches": researches, "user": current_user, "current_user": current_user}
    )


@router.get("/pesquisas/new", response_class=HTMLResponse)
async def new_research_form(
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    return templates.TemplateResponse(
        "procurement/research_form.html",
        {"request": request, "user": current_user, "current_user": current_user}
    )


@router.post("/pesquisas/new")
async def create_research_submit(
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    import shutil
    import os
    import uuid

    try:
        form_data = await request.form()
        titulo = form_data.get("titulo")
        justificativa = form_data.get("justificativa")

        if not titulo or not justificativa:
            raise ValueError("Título e Justificativa são obrigatórios.")

        # Buscar itens enviados dinamicamente
        indices = []
        for key in form_data.keys():
            if key.startswith("item_nome_"):
                try:
                    idx = int(key.split("_")[-1])
                    indices.append(idx)
                except ValueError:
                    pass

        items_in = []
        for idx in sorted(indices):
            nome = form_data.get(f"item_nome_{idx}")
            link = form_data.get(f"item_link_{idx}")
            
            valor_str = form_data.get(f"item_valor_{idx}") or "0.0"
            valor_estimado = float(valor_str.replace(",", "."))
            
            qtd_str = form_data.get(f"item_qtd_{idx}") or "1.0"
            quantidade = float(qtd_str.replace(",", "."))
            
            tipo_produto = form_data.get(f"item_tipo_{idx}") or "Consumo"

            # Upload da Imagem
            imagem_path = None
            foto_file = form_data.get(f"item_foto_{idx}")
            if foto_file and hasattr(foto_file, 'filename') and foto_file.filename:
                os.makedirs("static/uploads", exist_ok=True)
                filename = f"pesquisa_{uuid.uuid4().hex[:8]}_{foto_file.filename}"
                save_path = os.path.join("static/uploads", filename)
                with open(save_path, "wb") as f:
                    shutil.copyfileobj(foto_file.file, f)
                imagem_path = f"/static/uploads/{filename}"

            if nome:
                items_in.append(PurchaseResearchItemCreate(
                    nome_produto=nome,
                    link_produto=link,
                    imagem_path=imagem_path,
                    valor_estimado=valor_estimado,
                    quantidade=quantidade,
                    tipo_produto=tipo_produto
                ))

        if not items_in:
            raise ValueError("A pesquisa precisa conter pelo menos um produto.")

        research_create = PurchaseResearchCreate(
            titulo=titulo,
            justificativa=justificativa,
            items=items_in
        )

        status_val = form_data.get("status") or "Pendente"
        status = PurchaseResearchStatus.RASCUNHO if status_val == "Rascunho" else PurchaseResearchStatus.PENDENTE

        research = await crud_proc.create_purchase_research(db, research_create, current_user.id, status=status)
        # Registrar histórico
        await crud_proc.log_history(
            db, "purchase_researches", research.id, current_user.id, "Criou Pesquisa de Compra"
        )

        return RedirectResponse(url="/compras/pesquisas", status_code=303)
    except Exception as e:
        logger.error(f"Erro ao criar pesquisa de compra: {e}")
        return templates.TemplateResponse(
            "procurement/research_form.html",
            {
                "request": request,
                "current_user": current_user,
                "error": str(e)
            }
        )


@router.get("/pesquisas/{research_id}", response_class=HTMLResponse)
async def view_research(
    research_id: int,
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    research = await crud_proc.get_purchase_research(db, research_id)
    if not research:
        raise HTTPException(status_code=404, detail="Pesquisa não encontrada")

    cost_centers = (await db.execute(select(CostCenter).filter(CostCenter.alerta_limite == True))).scalars().all()
    # Caso a lista acima venha vazia, pegamos todos
    if not cost_centers:
        cost_centers = (await db.execute(select(CostCenter))).scalars().all()

    # Verificar se já existe uma SC originada desta pesquisa
    sc_vinculada = None
    if research.status == PurchaseResearchStatus.APROVADA:
        # Procurar SC cuja justificativa contenha o número da pesquisa
        sc_res = await db.execute(
            select(PurchaseRequest)
            .filter(PurchaseRequest.justificativa.like(f"%{research.numero}%"))
        )
        sc_vinculada = sc_res.scalars().first()

    return templates.TemplateResponse(
        "procurement/research_detail.html",
        {
            "request": request,
            "research": research,
            "user": current_user,
            "current_user": current_user,
            "cost_centers": cost_centers,
            "sc_vinculada": sc_vinculada
        }
    )

@router.post("/pesquisas/{research_id}/enviar")
async def send_research_for_approval(
    research_id: int,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    research = await crud_proc.get_purchase_research(db, research_id)
    if not research:
        raise HTTPException(status_code=404, detail="Pesquisa não encontrada")
        
    if research.status != PurchaseResearchStatus.RASCUNHO:
        raise HTTPException(status_code=400, detail="Esta pesquisa não está em rascunho")
        
    research.status = PurchaseResearchStatus.PENDENTE
    db.add(research)
    await db.commit()
    
    await crud_proc.log_history(
        db, "purchase_researches", research_id, current_user.id, "Enviou pesquisa para aprovação"
    )
    
    return RedirectResponse(url=f"/compras/pesquisas/{research_id}", status_code=303)

@router.post("/pesquisas/{research_id}/decidir")
async def decide_research(
    research_id: int,
    request: Request,
    current_user: Annotated[User, Depends(get_active_user_web)],
    db: Annotated[AsyncSession, Depends(get_db)]
):
    # Apenas gerentes/admins podem decidir
    if current_user.role not in [UserRole.ADMIN, UserRole.GERENTE, UserRole.DIRETOR]:
        raise HTTPException(status_code=403, detail="Acesso não autorizado")

    research = await crud_proc.get_purchase_research(db, research_id)
    if not research:
        raise HTTPException(status_code=404, detail="Pesquisa não encontrada")

    try:
        form_data = await request.form()
        acao = form_data.get("acao") # "aprovar" ou "rejeitar"
        justificativa_decisao = form_data.get("justificativa_decisao")
        centro_custo_id_str = form_data.get("centro_custo_id")
        
        if acao == "aprovar":
            if not centro_custo_id_str:
                raise ValueError("Centro de Custo é obrigatório para aprovação.")
            centro_custo_id = int(centro_custo_id_str)

            # Obter lista de IDs dos itens aprovados
            approved_item_ids = []
            for key in form_data.keys():
                if key.startswith("approve_item_"):
                    try:
                        item_id = int(key.split("_")[-1])
                        approved_item_ids.append(item_id)
                    except ValueError:
                        pass

            if not approved_item_ids:
                raise ValueError("Selecione pelo menos um produto para aprovar.")

            # Chamar conversão
            sc = await serv_proc.convert_research_to_purchase_request(
                research_id=research_id,
                db=db,
                current_user_id=current_user.id,
                approved_item_ids=approved_item_ids,
                centro_custo_id=centro_custo_id,
                justificativa=justificativa_decisao
            )
            
            await crud_proc.log_history(
                db, "purchase_researches", research_id, current_user.id, "Aprovou Pesquisa e gerou Solicitação"
            )
        else:
            # Rejeitar
            research.status = PurchaseResearchStatus.REPROVADA
            db.add(research)
            await db.commit()
            
            await crud_proc.log_history(
                db, "purchase_researches", research_id, current_user.id, f"Rejeitou Pesquisa: {justificativa_decisao or ''}"
            )

        return RedirectResponse(url=f"/compras/pesquisas/{research_id}", status_code=303)
    except Exception as e:
        logger.error(f"Erro ao decidir pesquisa: {e}")
        cost_centers = (await db.execute(select(CostCenter))).scalars().all()
        return templates.TemplateResponse(
            "procurement/research_detail.html",
            {
                "request": request,
                "research": research,
                "user": current_user,
                "current_user": current_user,
                "cost_centers": cost_centers,
                "error": str(e)
            }
        )


