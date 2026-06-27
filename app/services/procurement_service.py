# app/services/procurement_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from datetime import datetime
from typing import List, Dict, Any, Optional

from app.models.procurement import (
    PurchaseRequest, PurchaseRequestItem, PurchaseQuotation, PurchaseQuotationSupplier,
    PurchaseQuotationItem, PurchaseOrder, PurchaseOrderItem, PurchaseReceiving,
    PurchaseReceivingItem, PurchaseCategory, PurchaseProduct, CostCenter,
    ProductType, MaterialStock, MaterialStockTransaction, PurchaseRequestStatus
)
from app.models.asset import Asset, AssetStatus
from app.models.maintenance import Manutencao
from app.models.service_desk import ServiceTicket
from app.crud.procurement import generate_request_number, create_or_update_stock

async def calculate_quotation_comparison(quotation_id: int, db: AsyncSession) -> Dict[str, Any]:
    """
    Retorna o comparativo completo de cotações para uma Cotação (CQ) e destaca os vencedores
    por menor preço, menor prazo e melhor custo-benefício.
    """
    # Buscar cotação
    result = await db.execute(
        select(PurchaseQuotation)
        .options(
            selectinload(PurchaseQuotation.suppliers).selectinload(PurchaseQuotationSupplier.fornecedor),
            selectinload(PurchaseQuotation.suppliers).selectinload(PurchaseQuotationSupplier.itens).selectinload(PurchaseQuotationItem.product)
        )
        .filter(PurchaseQuotation.id == quotation_id)
    )
    quotation = result.scalars().first()
    if not quotation:
        return {}

    suppliers = quotation.suppliers
    if not suppliers:
        return {"quotation": quotation, "suppliers": []}

    # Determinar vencedor por menor preço
    cheapest_supplier = min(suppliers, key=lambda s: s.valor_total) if suppliers else None
    
    # Determinar vencedor por menor prazo
    fastest_supplier = min(suppliers, key=lambda s: s.prazo_entrega_dias) if suppliers else None
    
    # Custo-benefício (combinação linear simples: menor preco/total com peso e menor prazo com peso)
    # score = (valor_total * 0.7) + (prazo_entrega_dias * 100 * 0.3)
    best_value_supplier = None
    if suppliers:
        best_value_supplier = min(suppliers, key=lambda s: (float(s.valor_total) * 0.7) + (s.prazo_entrega_dias * 50 * 0.3))

    return {
        "quotation": quotation,
        "suppliers": suppliers,
        "cheapest_id": cheapest_supplier.id if cheapest_supplier else None,
        "fastest_id": fastest_supplier.id if fastest_supplier else None,
        "best_value_id": best_value_supplier.id if best_value_supplier else None
    }

async def convert_receiving_to_assets(receiving_id: int, db: AsyncSession, current_user_id: int) -> List[Asset]:
    """
    Processa os itens de um recebimento de compras. 
    Se o produto for do tipo EQUIPAMENTO, cria automaticamente registros na tabela assets (Gestão de Ativos)
    e vincula o ID do ativo gerado de volta ao item recebido.
    """
    result = await db.execute(
        select(PurchaseReceiving)
        .options(
            selectinload(PurchaseReceiving.order).selectinload(PurchaseOrder.centro_custo),
            selectinload(PurchaseReceiving.itens).selectinload(PurchaseReceivingItem.product)
        )
        .filter(PurchaseReceiving.id == receiving_id)
    )
    receiving = result.scalars().first()
    if not receiving:
        return []

    created_assets = []
    
    # Obter total de assets existentes para gerar patrimonio sequencial
    asset_count_res = await db.execute(select(Asset))
    current_count = len(asset_count_res.scalars().all())

    for item in receiving.itens:
        # Só cria ativo automaticamente para Equipamentos
        if item.product.tipo == ProductType.EQUIPAMENTO:
            # Gerar serial/patrimonio sequencial
            current_count += 1
            patrimonio_tag = f"PAT-{datetime.now().year}-{current_count:04d}"
            
            # Criar Ativo
            db_asset = Asset(
                nome=item.product.nome,
                e_patrimonio=patrimonio_tag,
                modelo=item.product.modelo,
                descricao=item.product.descricao or f"Criado automaticamente pelo recebimento do Pedido {receiving.order.numero}",
                data_aquisicao=datetime.now(),
                valor=float(receiving.order.valor_total / len(receiving.order.itens)) if receiving.order.itens else 0.0,
                status=AssetStatus.ARMAZENADO,
                numero_serie=item.product.codigo,
                fornecedor_id=receiving.order.fornecedor_id,
                nota_fiscal_id=receiving.nota_fiscal_id,
                created_by_id=current_user_id,
                current_departamento_id=receiving.order.centro_custo.departamento_id
            )
            db.add(db_asset)
            await db.flush() # Gerar ID do ativo
            
            item.ativo_criado_id = db_asset.id
            db.add(item)
            created_assets.append(db_asset)
        
        # Se for material de consumo (ex: lâmpada), entra no estoque simples de almoxarifado
        elif item.product.tipo == ProductType.MATERIAL_CONSUMO:
            await create_or_update_stock(
                db=db,
                product_id=item.product_id,
                quantidade=float(item.quantidade_recebida),
                tipo="Entrada",
                user_id=current_user_id,
                justificativa=f"Entrada por Recebimento {receiving.id} do Pedido {receiving.order.numero}",
                origem_tabela="purchase_receivings",
                origem_id=receiving.id
            )
            item.estoque_atualizado = True
            db.add(item)

    await db.commit()
    return created_assets

async def handle_material_consumption_in_maintenance(
    product_id: int, quantity: float, db: AsyncSession, current_user_id: int, maintenance_id: int
) -> Optional[MaterialStock]:
    """
    Abate a quantidade do estoque físico quando o item for utilizado em uma manutenção.
    """
    # Validar se existe estoque disponível
    stock = await db.execute(select(MaterialStock).filter(MaterialStock.product_id == product_id))
    stock_obj = stock.scalars().first()
    if not stock_obj or stock_obj.quantidade_saldo < quantity:
        return None # Saldo insuficiente
        
    updated_stock = await create_or_update_stock(
        db=db,
        product_id=product_id,
        quantidade=quantity,
        tipo="Saída",
        user_id=current_user_id,
        justificativa=f"Consumo na Manutenção ID {maintenance_id}",
        origem_tabela="maintenance",
        origem_id=maintenance_id
    )
    return updated_stock

async def create_purchase_request_from_os(
    os_id: int, items_data: List[Dict[str, Any]], db: AsyncSession, solicitante_id: int
) -> PurchaseRequest:
    """
    Cria uma Solicitação de Compra vinculada a uma Ordem de Serviço da Manutenção.
    """
    # Encontrar OS para extrair departamento
    os_res = await db.execute(select(Manutencao).filter(Manutencao.id == os_id))
    os_obj = os_res.scalars().first()
    dept_id = os_obj.asset.current_departamento_id if (os_obj and os_obj.asset) else 1
    
    # Obter um centro de custo padrão do departamento
    cc_res = await db.execute(select(CostCenter).filter(CostCenter.departamento_id == dept_id))
    cc_obj = cc_res.scalars().first()
    cc_id = cc_obj.id if cc_obj else 1

    num = await generate_request_number(db)
    db_req = PurchaseRequest(
        numero=num,
        solicitante_id=solicitante_id,
        departamento_id=dept_id,
        centro_custo_id=cc_id,
        justificativa=f"Solicitação de peças/serviços para atendimento da Ordem de Serviço ID {os_id}",
        urgencia="Alta",
        status=PurchaseRequestStatus.PENDENTE,
        origem_os_id=os_id
    )
    db.add(db_req)
    await db.flush()

    for item in items_data:
        db_item = PurchaseRequestItem(
            request_id=db_req.id,
            product_id=item["product_id"],
            quantidade=item["quantidade"],
            valor_estimado=item["valor_estimado"],
            observacao=item.get("observacao", "")
        )
        db.add(db_item)

    await db.commit()
    await db.refresh(db_req)
    return db_req

async def create_purchase_request_from_ticket(
    ticket_id: int, items_data: List[Dict[str, Any]], db: AsyncSession, solicitante_id: int
) -> PurchaseRequest:
    """
    Cria uma Solicitação de Compra vinculada a um Chamado do Service Desk.
    """
    ticket_res = await db.execute(select(ServiceTicket).filter(ServiceTicket.id == ticket_id))
    ticket_obj = ticket_res.scalars().first()
    dept_id = ticket_obj.departamento_id if ticket_obj else 1

    cc_res = await db.execute(select(CostCenter).filter(CostCenter.departamento_id == dept_id))
    cc_obj = cc_res.scalars().first()
    cc_id = cc_obj.id if cc_obj else 1

    num = await generate_request_number(db)
    db_req = PurchaseRequest(
        numero=num,
        solicitante_id=solicitante_id,
        departamento_id=dept_id,
        centro_custo_id=cc_id,
        justificativa=f"Aquisição de equipamentos/insumos para atendimento ao Chamado ID {ticket_id}",
        urgencia="Média",
        status=PurchaseRequestStatus.PENDENTE,
        origem_ticket_id=ticket_id
    )
    db.add(db_req)
    await db.flush()

    for item in items_data:
        db_item = PurchaseRequestItem(
            request_id=db_req.id,
            product_id=item["product_id"],
            quantidade=item["quantidade"],
            valor_estimado=item["valor_estimado"],
            observacao=item.get("observacao", "")
        )
        db.add(db_item)

    await db.commit()
    await db.refresh(db_req)
    return db_req
