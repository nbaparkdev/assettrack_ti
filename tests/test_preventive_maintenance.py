import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.crud import user as user_crud
from app.schemas.user import UserCreate
from app.models.preventive_maintenance import MaintenanceOrder, MaintenanceMaterial, OrderStatus
from app.models.procurement import PurchaseProduct, MaterialStock
from app.crud.procurement import create_or_update_stock

@pytest.fixture
async def admin_user(db_session: AsyncSession):
    user_in = UserCreate(
        nome="Admin User",
        email="admin_pm_test@example.com",
        password="adminpass",
        role="admin",
        is_active=True
    )
    user = await user_crud.user.create(db_session, obj_in=user_in)
    return user

@pytest.fixture
async def admin_client(client: AsyncClient, admin_user):
    # Log in to get session cookie/token
    response = await client.post("/login", data={
        "email": "admin_pm_test@example.com", 
        "password": "adminpass"
    })
    return client

@pytest.mark.asyncio
async def test_maintenance_material_stock_flow(admin_client: AsyncClient, db_session: AsyncSession):
    # 1. Criar produto no banco
    product = PurchaseProduct(
        nome="Filtro de Ar Condicionado",
        codigo="FILTRO-001",
        unidade="UN",
        categoria="Consumo",
        especificacao="Filtro de ar para manutenção de infra predial"
    )
    db_session.add(product)
    await db_session.flush()

    # 2. Registrar entrada de estoque (10 unidades)
    await create_or_update_stock(
        db=db_session,
        product_id=product.id,
        quantidade=10.0,
        tipo="Entrada",
        user_id=1,
        justificativa="Entrada inicial de testes"
    )
    await db_session.commit()

    # Verificar estoque inicial
    stock_res = await db_session.execute(select(MaterialStock).filter(MaterialStock.product_id == product.id))
    stock_obj = stock_res.scalar_one()
    assert stock_obj.quantidade_saldo == 10.0

    # 3. Criar Ordem de Serviço
    order = MaintenanceOrder(
        numero="OS-2026-99999",
        tipo="Corretiva",
        status=OrderStatus.ABERTA,
        prioridade="Alta",
        criticidade="Média",
        descricao="Manutenção predial ar condicionado sala 2",
        infra_predial_servico="Limpeza e troca de filtro de ar",
        custo_total=0.0
    )
    db_session.add(order)
    await db_session.commit()

    # 4. Adicionar Material Consumido do Estoque (3 unidades a R$ 50.00 cada)
    payload = {
        "product_id": product.id,
        "quantidade": 3.0,
        "valor_unitario": 50.00,
        "observacao": "Troca preventiva"
    }
    response = await admin_client.post(f"/manutencao-preventiva/ordens/{order.id}/materiais", data=payload)
    assert response.status_code == 303

    # Recarregar sessão para verificar alterações
    await db_session.close()
    
    # 5. Validar redução do estoque (deve ser 7 unidades)
    stock_res = await db_session.execute(select(MaterialStock).filter(MaterialStock.product_id == product.id))
    stock_obj = stock_res.scalar_one()
    assert stock_obj.quantidade_saldo == 7.0

    # 6. Validar que o custo da OS foi atualizado (3 * 50.00 = 150.00)
    order_res = await db_session.execute(select(MaintenanceOrder).filter(MaintenanceOrder.id == order.id))
    order_obj = order_res.scalar_one()
    assert order_obj.custo_total == 150.00

    # 7. Remover o material e validar estorno do estoque (deve voltar para 10 unidades)
    # Buscar material criado
    mat_res = await db_session.execute(select(MaintenanceMaterial).filter(MaintenanceMaterial.order_id == order.id))
    material = mat_res.scalar_one()

    # Deletar material
    response = await admin_client.post(f"/manutencao-preventiva/ordens/{order.id}/materiais/{material.id}/delete")
    assert response.status_code == 303

    # Recarregar estoque
    stock_res = await db_session.execute(select(MaterialStock).filter(MaterialStock.product_id == product.id))
    stock_obj = stock_res.scalar_one()
    assert stock_obj.quantidade_saldo == 10.0

    # Recarregar ordem
    order_res = await db_session.execute(select(MaintenanceOrder).filter(MaintenanceOrder.id == order.id))
    order_obj = order_res.scalar_one()
    assert order_obj.custo_total == 0.0
