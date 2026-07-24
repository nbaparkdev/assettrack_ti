import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.procurement import (
    PurchaseResearch, PurchaseResearchItem, PurchaseResearchStatus,
    PurchaseRequest, PurchaseProduct, ProductType, MaterialStock,
    MaterialStockTransaction, CostCenter
)
from app.schemas.procurement import (
    PurchaseResearchCreate, PurchaseResearchItemCreate
)
from app.crud import procurement as crud_proc
from app.services import procurement_service as serv_proc

@pytest.mark.asyncio
async def test_create_and_convert_purchase_research(db_session: AsyncSession):
    # 1. Create a Cost Center (needed for conversion)
    cc = CostCenter(
        nome="TI Infra",
        codigo="TI01",
        orcamento_mensal=10000.0,
        orcamento_mensal_usado=0.0,
        alerta_limite=True
    )
    db_session.add(cc)
    await db_session.commit()
    await db_session.refresh(cc)

    # 2. Create the PurchaseResearch request
    item_1 = PurchaseResearchItemCreate(
        nome_produto="Monitor Dell 27",
        link_produto="https://dell.com/monitor",
        imagem_path="/static/uploads/dell.png",
        valor_estimado=1500.00,
        quantidade=2,
        tipo_produto="Imobilizado"
    )
    item_2 = PurchaseResearchItemCreate(
        nome_produto="Teclado Mecânico Logitech",
        link_produto="https://logitech.com/keyboard",
        imagem_path=None,
        valor_estimado=450.00,
        quantidade=5,
        tipo_produto="Consumo"
    )

    research_in = PurchaseResearchCreate(
        titulo="Upgrade Monitores e Teclados 2026",
        justificativa="Necessidade de novos equipamentos e suprimentos periféricos para a equipe de desenvolvimento.",
        items=[item_1, item_2]
    )

    research = await crud_proc.create_purchase_research(
        db=db_session,
        obj_in=research_in,
        solicitante_id=1
    )

    assert research.id is not None
    assert research.numero.startswith("PQ-")
    assert research.status == PurchaseResearchStatus.PENDENTE
    assert len(research.items) == 2

    # Verify item properties
    item_imob = next(i for i in research.items if i.tipo_produto == "Imobilizado")
    item_cons = next(i for i in research.items if i.tipo_produto == "Consumo")

    assert item_imob.nome_produto == "Monitor Dell 27"
    assert item_cons.nome_produto == "Teclado Mecânico Logitech"

    # 3. Convert Research to PurchaseRequest
    approved_item_ids = [item_imob.id, item_cons.id]
    
    sc = await serv_proc.convert_research_to_purchase_request(
        research_id=research.id,
        db=db_session,
        current_user_id=1,
        approved_item_ids=approved_item_ids,
        centro_custo_id=cc.id,
        justificativa="Aprovado em comissão de compras"
    )

    assert sc is not None
    assert sc.status.value == "Aprovada"
    assert sc.centro_custo_id == cc.id
    assert len(sc.itens) == 2

    # 4. Check if the Products (PurchaseProduct) were created correctly
    products_res = await db_session.execute(select(PurchaseProduct))
    products = products_res.scalars().all()
    assert len(products) == 2

    prod_imob = next(p for p in products if p.nome == "Monitor Dell 27")
    prod_cons = next(p for p in products if p.nome == "Teclado Mecânico Logitech")

    assert prod_imob.tipo == ProductType.EQUIPAMENTO
    assert prod_cons.tipo == ProductType.MATERIAL_CONSUMO
    assert prod_imob.imagem_path == "/static/uploads/dell.png"

    # 5. Check stock initialization for Consumo
    stock_res = await db_session.execute(select(MaterialStock).filter(MaterialStock.product_id == prod_cons.id))
    stock = stock_res.scalars().first()
    assert stock is not None
    assert stock.quantidade_saldo == 0.00

    tx_res = await db_session.execute(
        select(MaterialStockTransaction).filter(MaterialStockTransaction.product_id == prod_cons.id)
    )
    tx = tx_res.scalars().first()
    assert tx is not None
    assert tx.tipo_movimentacao == "Entrada"
    assert tx.quantidade == 0.00

    # Check that no stock was created for Equipamento/Imobilizado
    stock_imob_res = await db_session.execute(select(MaterialStock).filter(MaterialStock.product_id == prod_imob.id))
    stock_imob = stock_imob_res.scalars().first()
    assert stock_imob is None

    # Check status of the research
    assert research.status == PurchaseResearchStatus.APROVADA


@pytest.mark.asyncio
async def test_convert_research_reuses_existing_product(db_session: AsyncSession):
    # 1. Create a Cost Center
    cc = CostCenter(
        nome="TI Infra",
        codigo="TI01",
        orcamento_mensal=10000.0,
        orcamento_mensal_usado=0.0,
        alerta_limite=True
    )
    db_session.add(cc)
    
    # 2. Pre-create a PurchaseProduct with the same name
    existing_product = PurchaseProduct(
        codigo="PRD-EXISTING123",
        nome="Monitor Dell 27",
        categoria_id=1,
        unidade="UN",
        tipo=ProductType.EQUIPAMENTO,
        ativo=True
    )
    db_session.add(existing_product)
    await db_session.commit()

    # 3. Create a Research Request containing that product name
    item = PurchaseResearchItemCreate(
        nome_produto="Monitor Dell 27",
        link_produto="https://dell.com/monitor",
        imagem_path=None,
        valor_estimado=1500.00,
        quantidade=1,
        tipo_produto="Imobilizado"
    )

    research_in = PurchaseResearchCreate(
        titulo="Research referencing existing product",
        justificativa="Test case justifications",
        items=[item]
    )

    research = await crud_proc.create_purchase_research(
        db=db_session,
        obj_in=research_in,
        solicitante_id=1
    )

    # 4. Convert Research to PurchaseRequest
    sc = await serv_proc.convert_research_to_purchase_request(
        research_id=research.id,
        db=db_session,
        current_user_id=1,
        approved_item_ids=[research.items[0].id],
        centro_custo_id=cc.id,
        justificativa="Approved referencing existing product"
    )

    assert sc is not None
    assert len(sc.itens) == 1
    assert sc.itens[0].product_id == existing_product.id

    # Verify no new product was created
    products_res = await db_session.execute(select(PurchaseProduct))
    products = products_res.scalars().all()
    assert len(products) == 1
    assert products[0].codigo == "PRD-EXISTING123"

