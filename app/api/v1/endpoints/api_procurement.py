# app/api/v1/endpoints/api_procurement.py
from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import dependencies
from app.database import get_db
from app.crud import procurement as crud_proc
from app.services import procurement_service as serv_proc
from app.schemas.procurement import (
    PurchaseCategoryCreate, PurchaseCategoryResponse,
    PurchaseProductCreate, PurchaseProductResponse,
    CostCenterCreate, CostCenterResponse,
    PurchaseRequestCreate, PurchaseRequestResponse,
    PurchaseOrderCreate, PurchaseOrderResponse,
    PurchaseReceivingCreate, PurchaseReceivingResponse,
    PurchaseContractCreate, PurchaseContractResponse,
    MaterialStockResponse
)

router = APIRouter()

async def api_check_purchases_enabled(request: Request):
    if not getattr(request.app.state, "purchases_enabled", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Módulo de Compras (Procurement) está desativado pelo Administrador."
        )

# Apply check_purchases_enabled to all endpoints in this router
router.dependencies.append(Depends(api_check_purchases_enabled))

# ----------
# CATEGORIES
# ----------
@router.get("/categories", response_model=List[PurchaseCategoryResponse])
async def read_categories(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dependencies.User, Depends(dependencies.get_current_active_user)],
    skip: int = 0, limit: int = 100
):
    return await crud_proc.get_categories(db, skip=skip, limit=limit)

@router.post("/categories", response_model=PurchaseCategoryResponse)
async def create_category(
    category_in: PurchaseCategoryCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dependencies.User, Depends(dependencies.get_current_active_manager_or_superuser)]
):
    return await crud_proc.create_category(db, category=category_in)

# --------
# PRODUCTS
# --------
@router.get("/products", response_model=List[PurchaseProductResponse])
async def read_products(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dependencies.User, Depends(dependencies.get_current_active_user)],
    skip: int = 0, limit: int = 100
):
    return await crud_proc.get_products(db, skip=skip, limit=limit)

@router.post("/products", response_model=PurchaseProductResponse)
async def create_product(
    product_in: PurchaseProductCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dependencies.User, Depends(dependencies.get_current_active_manager_or_superuser)]
):
    # Check if code already exists
    existing = await crud_proc.get_product_by_codigo(db, codigo=product_in.codigo)
    if existing:
        raise HTTPException(status_code=400, detail="Código de produto já cadastrado")
    return await crud_proc.create_product(db, product=product_in)

# ------------
# COST CENTERS
# ------------
@router.get("/cost-centers", response_model=List[CostCenterResponse])
async def read_cost_centers(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dependencies.User, Depends(dependencies.get_current_active_user)],
    skip: int = 0, limit: int = 100
):
    return await crud_proc.get_cost_centers(db, skip=skip, limit=limit)

@router.post("/cost-centers", response_model=CostCenterResponse)
async def create_cost_center(
    cc_in: CostCenterCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dependencies.User, Depends(dependencies.get_current_active_manager_or_superuser)]
):
    return await crud_proc.create_cost_center(db, cc=cc_in)

# -----------------
# PURCHASE REQUESTS
# -----------------
@router.get("/requests", response_model=List[PurchaseRequestResponse])
async def read_requests(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dependencies.User, Depends(dependencies.get_current_active_user)],
    skip: int = 0, limit: int = 100
):
    return await crud_proc.get_purchase_requests(db, skip=skip, limit=limit)

@router.post("/requests", response_model=PurchaseRequestResponse)
async def create_purchase_request(
    request_in: PurchaseRequestCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dependencies.User, Depends(dependencies.get_current_active_user)]
):
    # Validar limite orçamentário do centro de custo
    cc = await crud_proc.get_cost_center(db, cc_id=request_in.centro_custo_id)
    if not cc:
        raise HTTPException(status_code=404, detail="Centro de Custo não encontrado")
        
    estimated_total = sum(item.quantidade * item.valor_estimado for item in request_in.itens)
    
    # Se limite excedido e bloquear ativado, barrar a criação exceto se for gerente/admin
    if cc.bloquear_limite and (cc.orcamento_mensal_usado + estimated_total > cc.orcamento_mensal):
        if current_user.role.value.lower() not in ["admin", "gerente_ti", "comprador"]:
            raise HTTPException(
                status_code=400,
                detail=f"Criação bloqueada: O valor total estimado R$ {estimated_total:.2f} excede o limite mensal restante do Centro de Custo."
            )
            
    req = await crud_proc.create_purchase_request(
        db, request_in=request_in, solicitante_id=current_user.id, departamento_id=current_user.departamento_id or 1
    )
    await crud_proc.log_history(
        db, tabela="purchase_requests", registro_id=req.id, user_id=current_user.id, acao="Solicitação Criada"
    )
    return req

# ---------------
# PURCHASE ORDERS
# ---------------
@router.get("/orders", response_model=List[PurchaseOrderResponse])
async def read_orders(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dependencies.User, Depends(dependencies.get_current_active_user)],
    skip: int = 0, limit: int = 100
):
    return await crud_proc.get_purchase_orders(db, skip=skip, limit=limit)

@router.post("/orders", response_model=PurchaseOrderResponse)
async def create_purchase_order(
    order_in: PurchaseOrderCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dependencies.User, Depends(dependencies.get_current_active_manager_or_superuser)]
):
    order = await crud_proc.create_purchase_order(db, order_in=order_in)
    await crud_proc.log_history(
        db, tabela="purchase_orders", registro_id=order.id, user_id=current_user.id, acao="Pedido Emitido"
    )
    return order

# ------------------
# PURCHASE RECEIVING
# ------------------
@router.post("/receivings", response_model=PurchaseReceivingResponse)
async def create_purchase_receiving(
    receiving_in: PurchaseReceivingCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dependencies.User, Depends(dependencies.get_current_active_user)]
):
    rec = await crud_proc.create_receiving(db, receiving_in=receiving_in, responsavel_id=current_user.id)
    # Trigger Asset Creation & Stock Addition
    await serv_proc.convert_receiving_to_assets(rec.id, db, current_user.id)
    
    await crud_proc.log_history(
        db, tabela="purchase_receivings", registro_id=rec.id, user_id=current_user.id, acao="Recebimento Registrado"
    )
    return rec

# ---------
# CONTRACTS
# ---------
@router.get("/contracts", response_model=List[PurchaseContractResponse])
async def read_contracts(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dependencies.User, Depends(dependencies.get_current_active_user)],
    skip: int = 0, limit: int = 100
):
    return await crud_proc.get_contracts(db, skip=skip, limit=limit)

@router.post("/contracts", response_model=PurchaseContractResponse)
async def create_contract(
    contract_in: PurchaseContractCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[dependencies.User, Depends(dependencies.get_current_active_manager_or_superuser)]
):
    return await crud_proc.create_contract(db, contract=contract_in)
