# app/crud/procurement.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import selectinload
from typing import List, Optional
from app.models.procurement import (
    PurchaseCategory, PurchaseProduct, CostCenter, PurchaseRequest, PurchaseRequestItem,
    PurchaseApproval, PurchaseQuotation, PurchaseQuotationSupplier, PurchaseQuotationItem,
    PurchaseOrder, PurchaseOrderItem, PurchaseReceiving, PurchaseReceivingItem,
    PurchaseContract, MaterialStock, MaterialStockTransaction, PurchaseHistory,
    PurchaseRequestStatus, PurchaseOrderStatus, PurchaseUnit
)
from app.schemas.procurement import (
    PurchaseCategoryCreate, PurchaseCategoryUpdate,
    PurchaseProductCreate, PurchaseProductUpdate,
    CostCenterCreate, CostCenterUpdate,
    PurchaseRequestCreate, PurchaseRequestUpdate,
    PurchaseOrderCreate, PurchaseReceivingCreate,
    PurchaseContractCreate
)

# -----------------
# PURCHASE CATEGORY
# -----------------
async def get_category(db: AsyncSession, category_id: int) -> Optional[PurchaseCategory]:
    result = await db.execute(select(PurchaseCategory).filter(PurchaseCategory.id == category_id))
    return result.scalars().first()

async def get_categories(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[PurchaseCategory]:
    result = await db.execute(select(PurchaseCategory).offset(skip).limit(limit))
    return result.scalars().all()

async def create_category(db: AsyncSession, category: PurchaseCategoryCreate) -> PurchaseCategory:
    db_cat = PurchaseCategory(**category.model_dump())
    db.add(db_cat)
    await db.commit()
    await db.refresh(db_cat)
    return db_cat

async def update_category(db: AsyncSession, db_cat: PurchaseCategory, category: PurchaseCategoryUpdate) -> PurchaseCategory:
    update_data = category.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_cat, key, value)
    await db.commit()
    await db.refresh(db_cat)
    return db_cat


# -------------
# PURCHASE UNIT
# -------------
async def get_units(db: AsyncSession) -> List[PurchaseUnit]:
    result = await db.execute(select(PurchaseUnit).order_by(PurchaseUnit.sigla))
    return result.scalars().all()

async def create_unit(db: AsyncSession, sigla: str, descricao: Optional[str] = None) -> PurchaseUnit:
    db_unit = PurchaseUnit(sigla=sigla.upper(), descricao=descricao)
    db.add(db_unit)
    await db.commit()
    await db.refresh(db_unit)
    return db_unit


# ----------------
# PURCHASE PRODUCT
# ----------------
async def get_product(db: AsyncSession, product_id: int) -> Optional[PurchaseProduct]:
    result = await db.execute(
        select(PurchaseProduct)
        .options(selectinload(PurchaseProduct.categoria))
        .filter(PurchaseProduct.id == product_id)
    )
    return result.scalars().first()

async def get_product_by_codigo(db: AsyncSession, codigo: str) -> Optional[PurchaseProduct]:
    result = await db.execute(select(PurchaseProduct).filter(PurchaseProduct.codigo == codigo))
    return result.scalars().first()

async def get_products(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[PurchaseProduct]:
    result = await db.execute(
        select(PurchaseProduct)
        .options(selectinload(PurchaseProduct.categoria))
        .offset(skip).limit(limit)
    )
    return result.scalars().all()

async def create_product(db: AsyncSession, product: PurchaseProductCreate) -> PurchaseProduct:
    db_prod = PurchaseProduct(**product.model_dump())
    db.add(db_prod)
    await db.commit()
    await db.refresh(db_prod)
    return db_prod

async def update_product(db: AsyncSession, db_prod: PurchaseProduct, product: PurchaseProductUpdate) -> PurchaseProduct:
    update_data = product.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_prod, key, value)
    await db.commit()
    await db.refresh(db_prod)
    return db_prod


# -----------
# COST CENTER
# -----------
async def get_cost_center(db: AsyncSession, cc_id: int) -> Optional[CostCenter]:
    result = await db.execute(
        select(CostCenter)
        .options(selectinload(CostCenter.departamento), selectinload(CostCenter.responsavel))
        .filter(CostCenter.id == cc_id)
    )
    return result.scalars().first()

async def get_cost_centers(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[CostCenter]:
    result = await db.execute(
        select(CostCenter)
        .options(selectinload(CostCenter.departamento), selectinload(CostCenter.responsavel))
        .offset(skip).limit(limit)
    )
    return result.scalars().all()

async def create_cost_center(db: AsyncSession, cc: CostCenterCreate) -> CostCenter:
    db_cc = CostCenter(**cc.model_dump())
    db.add(db_cc)
    await db.commit()
    await db.refresh(db_cc)
    return db_cc

async def update_cost_center(db: AsyncSession, db_cc: CostCenter, cc: CostCenterUpdate) -> CostCenter:
    update_data = cc.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_cc, key, value)
    await db.commit()
    await db.refresh(db_cc)
    return db_cc


# ----------------
# PURCHASE REQUEST
# ----------------
async def get_purchase_request(db: AsyncSession, request_id: int) -> Optional[PurchaseRequest]:
    result = await db.execute(
        select(PurchaseRequest)
        .options(
            selectinload(PurchaseRequest.solicitante),
            selectinload(PurchaseRequest.departamento),
            selectinload(PurchaseRequest.centro_custo),
            selectinload(PurchaseRequest.itens).selectinload(PurchaseRequestItem.product),
            selectinload(PurchaseRequest.approvals).selectinload(PurchaseApproval.aprovador),
            selectinload(PurchaseRequest.origem_os),
            selectinload(PurchaseRequest.origem_ticket)
        )
        .filter(PurchaseRequest.id == request_id)
    )
    return result.scalars().first()

async def get_purchase_requests(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[PurchaseRequest]:
    result = await db.execute(
        select(PurchaseRequest)
        .options(
            selectinload(PurchaseRequest.solicitante),
            selectinload(PurchaseRequest.departamento),
            selectinload(PurchaseRequest.centro_custo),
            selectinload(PurchaseRequest.itens)
        )
        .order_by(desc(PurchaseRequest.data_criacao))
        .offset(skip).limit(limit)
    )
    return result.scalars().all()

async def generate_request_number(db: AsyncSession) -> str:
    from datetime import datetime
    year = datetime.now().year
    prefix = f"SC-{year}-"
    # Find count of SCs this year
    result = await db.execute(
        select(PurchaseRequest).filter(PurchaseRequest.numero.like(f"{prefix}%"))
    )
    count = len(result.scalars().all()) + 1
    return f"{prefix}{count:06d}"

async def create_purchase_request(
    db: AsyncSession, request_in: PurchaseRequestCreate, solicitante_id: int, departamento_id: int, status: Optional[PurchaseRequestStatus] = None
) -> PurchaseRequest:
    num = await generate_request_number(db)
    req_data = request_in.model_dump(exclude={"itens"})
    db_req = PurchaseRequest(
        numero=num,
        solicitante_id=solicitante_id,
        departamento_id=departamento_id,
        **req_data
    )
    if status:
        db_req.status = status
    else:
        db_req.status = PurchaseRequestStatus.PENDENTE
        
    db.add(db_req)
    await db.flush() # Get req ID
    
    for item in request_in.itens:
        db_item = PurchaseRequestItem(
            request_id=db_req.id,
            **item.model_dump()
        )
        db.add(db_item)
    
    await db.commit()
    await db.refresh(db_req)
    return db_req

async def update_purchase_request(
    db: AsyncSession, db_req: PurchaseRequest, request_in: PurchaseRequestUpdate
) -> PurchaseRequest:
    update_data = request_in.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_req, key, value)
    await db.commit()
    await db.refresh(db_req)
    return db_req


# --------------
# PURCHASE ORDER
# --------------
async def get_purchase_order(db: AsyncSession, order_id: int) -> Optional[PurchaseOrder]:
    result = await db.execute(
        select(PurchaseOrder)
        .options(
            selectinload(PurchaseOrder.fornecedor),
            selectinload(PurchaseOrder.centro_custo),
            selectinload(PurchaseOrder.request),
            selectinload(PurchaseOrder.quotation),
            selectinload(PurchaseOrder.receivings).selectinload(PurchaseReceiving.responsavel),
            selectinload(PurchaseOrder.receivings).selectinload(PurchaseReceiving.nota_fiscal),
            selectinload(PurchaseOrder.itens).selectinload(PurchaseOrderItem.product)
        )
        .filter(PurchaseOrder.id == order_id)
    )
    return result.scalars().first()

async def get_purchase_orders(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[PurchaseOrder]:
    result = await db.execute(
        select(PurchaseOrder)
        .options(
            selectinload(PurchaseOrder.fornecedor),
            selectinload(PurchaseOrder.centro_custo),
            selectinload(PurchaseOrder.request)
        )
        .order_by(desc(PurchaseOrder.data_emissao))
        .offset(skip).limit(limit)
    )
    return result.scalars().all()

async def generate_order_number(db: AsyncSession) -> str:
    from datetime import datetime
    year = datetime.now().year
    prefix = f"PC-{year}-"
    result = await db.execute(
        select(PurchaseOrder).filter(PurchaseOrder.numero.like(f"{prefix}%"))
    )
    count = len(result.scalars().all()) + 1
    return f"{prefix}{count:06d}"

async def create_purchase_order(
    db: AsyncSession, order_in: PurchaseOrderCreate
) -> PurchaseOrder:
    num = await generate_order_number(db)
    order_data = order_in.model_dump(exclude={"itens"})
    
    # Calculate Total Value from items
    total_val = 0.00
    for item in order_in.itens:
        total_val += (item.quantidade * item.valor_unitario)
    
    # Add taxes & freight, subtract discount
    total_val = total_val + order_in.frete + order_in.ipi + order_in.icms - order_in.desconto
    
    db_order = PurchaseOrder(
        numero=num,
        valor_total=total_val,
        **order_data
    )
    db.add(db_order)
    await db.flush()
    
    for item in order_in.itens:
        db_item = PurchaseOrderItem(
            order_id=db_order.id,
            total_item=(item.quantidade * item.valor_unitario),
            **item.model_dump()
        )
        db.add(db_item)
        
    await db.commit()
    await db.refresh(db_order)
    return db_order


# ------------------
# PURCHASE RECEIVING
# ------------------
async def create_receiving(
    db: AsyncSession, receiving_in: PurchaseReceivingCreate, responsavel_id: int
) -> PurchaseReceiving:
    db_rec = PurchaseReceiving(
        order_id=receiving_in.order_id,
        nota_fiscal_id=receiving_in.nota_fiscal_id,
        observacoes=receiving_in.observacoes,
        responsavel_id=responsavel_id
    )
    db.add(db_rec)
    await db.flush()
    
    for item in receiving_in.itens:
        db_item = PurchaseReceivingItem(
            receiving_id=db_rec.id,
            **item.model_dump()
        )
        db.add(db_item)
        
    await db.commit()
    await db.refresh(db_rec)
    return db_rec


# -----------------
# PURCHASE CONTRACT
# -----------------
async def get_contract(db: AsyncSession, contract_id: int) -> Optional[PurchaseContract]:
    result = await db.execute(
        select(PurchaseContract)
        .options(selectinload(PurchaseContract.fornecedor))
        .filter(PurchaseContract.id == contract_id)
    )
    return result.scalars().first()

async def get_contracts(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[PurchaseContract]:
    result = await db.execute(
        select(PurchaseContract)
        .options(selectinload(PurchaseContract.fornecedor))
        .order_by(PurchaseContract.data_fim)
        .offset(skip).limit(limit)
    )
    return result.scalars().all()

async def create_contract(db: AsyncSession, contract: PurchaseContractCreate) -> PurchaseContract:
    db_contract = PurchaseContract(**contract.model_dump())
    db.add(db_contract)
    await db.commit()
    await db.refresh(db_contract)
    return db_contract


# --------------
# MATERIAL STOCK
# --------------
async def get_material_stock(db: AsyncSession, product_id: int) -> Optional[MaterialStock]:
    result = await db.execute(select(MaterialStock).filter(MaterialStock.product_id == product_id))
    return result.scalars().first()

async def create_or_update_stock(
    db: AsyncSession, product_id: int, quantidade: float, tipo: str, user_id: int, justificativa: str, origem_tabela: str = None, origem_id: int = None
) -> MaterialStock:
    stock = await get_material_stock(db, product_id)
    if not stock:
        stock = MaterialStock(product_id=product_id, quantidade_saldo=0.0)
        db.add(stock)
        await db.flush()
        
    if tipo == "Entrada":
        stock.quantidade_saldo += quantidade
    else:
        stock.quantidade_saldo -= quantidade
        
    db.add(stock)
    
    # Save Transaction
    tx = MaterialStockTransaction(
        product_id=product_id,
        quantidade=quantidade,
        tipo_movimentacao=tipo,
        origem_tabela=origem_tabela,
        origem_id=origem_id,
        user_id=user_id,
        justificativa=justificativa
    )
    db.add(tx)
    
    await db.commit()
    await db.refresh(stock)
    return stock


# ---------
# AUDITORIA
# ---------
async def log_history(
    db: AsyncSession, tabela: str, registro_id: int, user_id: int, acao: str, ip: str = None, obs: str = None
):
    history = PurchaseHistory(
        tabela_origem=tabela,
        registro_id=registro_id,
        user_id=user_id,
        acao=acao,
        ip_address=ip,
        observacoes=obs
    )
    db.add(history)
    await db.commit()
