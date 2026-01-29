import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud import user as user_crud
from app.crud import asset as asset_crud
from app.schemas.user import UserCreate
from app.models.asset import AssetStatus

@pytest.fixture
async def admin_user(db_session: AsyncSession):
    user_in = UserCreate(
        nome="Admin User",
        email="admin_test@example.com",
        password="adminpass",
        role="admin",
        is_active=True
    )
    user = await user_crud.user.create(db_session, obj_in=user_in)
    return user

@pytest.fixture
async def admin_client(client: AsyncClient, admin_user):
    # Log in to get token
    response = await client.post("/login", data={
        "email": "admin_test@example.com", 
        "password": "adminpass"
    })
    return client

@pytest.mark.asyncio
async def test_create_asset(admin_client: AsyncClient, db_session: AsyncSession):
    # Act
    payload = {
        "nome": "Notebook Dell",
        "modelo": "Latitude 5420",
        "serial_number": "ABC12345",
        "descricao": "Laptop corporativo",
        "data_aquisicao": "2024-01-01",
        "valor_aquisicao": "5000.00"
    }
    response = await admin_client.post("/assets/new", data=payload)
    
    # Assert
    assert response.status_code == 303
    
    # Verify DB
    assets = await asset_crud.asset.get_multi(db_session)
    assert len(assets) == 1
    assert assets[0].nome == "Notebook Dell"
    assert assets[0].status == AssetStatus.DISPONIVEL

@pytest.mark.asyncio
async def test_create_asset_optional_fields_empty(admin_client: AsyncClient, db_session: AsyncSession):
    # Act
    payload = {
        "nome": "Mouse Logi",
        "modelo": "M100",
        "serial_number": "MOUSE999",
        "descricao": "",
        "data_aquisicao": "",
        "valor_aquisicao": ""
    }
    response = await admin_client.post("/assets/new", data=payload)
    
    # Assert
    assert response.status_code == 303
    
    # Verify DB
    assets = await asset_crud.asset.get_multi(db_session)
    asset = assets[0]
    assert asset.data_aquisicao is None

@pytest.mark.asyncio
async def test_maintenance_workflow(admin_client: AsyncClient, db_session: AsyncSession):
    # Arrange: Create available asset
    from app.schemas.asset import AssetCreate
    from datetime import date
    
    asset_in = AssetCreate(
        nome="Servidor",
        modelo="HP Proliant",
        serial_number="SRV001",
        status=AssetStatus.DISPONIVEL,
        data_aquisicao=date(2023, 1, 1),
        valor_aquisicao=10000.0
    )
    asset = await asset_crud.asset.create(db_session, obj_in=asset_in)
    
    # Act 1: Start Maintenance
    response = await admin_client.post(f"/assets/{asset.id}/maintenance/start")
    assert response.status_code == 303
    
    await db_session.refresh(asset)
    assert asset.status == AssetStatus.MANUTENCAO
    
    # Act 2: Finish Maintenance
    response = await admin_client.post(f"/assets/{asset.id}/maintenance/finish")
    assert response.status_code == 303
    
    await db_session.refresh(asset)
    assert asset.status == AssetStatus.DISPONIVEL
