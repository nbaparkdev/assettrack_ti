import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import user as user_crud
from app.crud.procurement import create_or_update_stock
from app.models.procurement import PurchaseCategory, PurchaseProduct
from app.schemas.user import UserCreate


@pytest.fixture
async def admin_user(db_session: AsyncSession):
    user_in = UserCreate(
        nome="Admin Stock Test",
        email="admin_stock_test@example.com",
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
        "email": "admin_stock_test@example.com", 
        "password": "adminpass"
    })
    return client

@pytest.mark.asyncio
async def test_export_stock_pdf(admin_client: AsyncClient, db_session: AsyncSession):
    # 1. Create a category and product
    category = PurchaseCategory(nome="Consumo")
    db_session.add(category)
    await db_session.flush()

    product = PurchaseProduct(
        nome="Papel A4 Reciclado",
        codigo="PAPEL-A4-REC",
        unidade="UN",
        categoria_id=category.id,
        descricao="Pacote de papel A4 reciclado 500 folhas"
    )
    db_session.add(product)
    await db_session.flush()

    # 2. Add stock balance
    await create_or_update_stock(
        db=db_session,
        product_id=product.id,
        quantidade=15.0,
        tipo="Entrada",
        user_id=1,
        justificativa="Estoque inicial de papel"
    )
    await db_session.commit()

    # 3. Call the PDF export endpoint
    response = await admin_client.get("/compras/estoque/exportar")
    
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/pdf"
    assert "attachment; filename=Relatorio_Estoque_" in response.headers["Content-Disposition"]
    assert len(response.content) > 0
