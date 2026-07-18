import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud import user as user_crud
from app.crud import asset as asset_crud
from app.crud.maintenance_request import maintenance_request
from app.schemas.user import UserCreate
from app.schemas.asset import AssetCreate
from app.models.asset import AssetStatus
from app.models.maintenance_request import StatusSolicitacaoManutencao
from datetime import date

@pytest.fixture
async def test_users(db_session: AsyncSession):
    # Create common user (solicitante)
    user_comum_in = UserCreate(
        nome="Usuario Comum",
        email="comum@example.com",
        password="password123",
        role="usuario_comum",
        is_active=True
    )
    user_comum = await user_crud.user.create(db_session, obj_in=user_comum_in)

    # Create technician user
    tecnico_in = UserCreate(
        nome="Tecnico TI",
        email="tecnico@example.com",
        password="password123",
        role="tecnico",
        is_active=True
    )
    tecnico = await user_crud.user.create(db_session, obj_in=tecnico_in)
    
    return {"comum": user_comum, "tecnico": tecnico}

@pytest.fixture
async def comum_client(client: AsyncClient, test_users):
    # Log in as common user
    await client.post("/login", data={
        "email": "comum@example.com", 
        "password": "password123"
    })
    return client

@pytest.fixture
async def tecnico_client(client: AsyncClient, test_users):
    # Log in as technician
    await client.post("/login", data={
        "email": "tecnico@example.com", 
        "password": "password123"
    })
    return client

@pytest.mark.asyncio
async def test_full_user_maintenance_workflow(
    comum_client: AsyncClient,
    tecnico_client: AsyncClient,
    db_session: AsyncSession,
    test_users
):
    # 1. Create an asset in use by the common user
    asset_in = AssetCreate(
        nome="Notebook de Teste",
        modelo="Dell Latitude",
        e_patrimonio="DELL_TEST_123",
        status=AssetStatus.EM_USO,
        data_aquisicao=date(2025, 1, 1),
        valor_aquisicao=5000.0,
        current_user_id=test_users["comum"].id
    )
    asset = await asset_crud.asset.create(db_session, obj_in=asset_in)

    # 2. Request maintenance as common user
    req_payload = {
        "asset_id": asset.id,
        "descricao": "Teclado parou de funcionar completamente após cair café.",
        "prioridade": "media"
    }
    response = await comum_client.post("/solicitar-manutencao", data=req_payload)
    assert response.status_code == 303

    # Fetch created maintenance request
    requests = await maintenance_request.list_by_user(db_session, user_id=test_users["comum"].id)
    assert len(requests) == 1
    maint_req = requests[0]
    assert maint_req.status == StatusSolicitacaoManutencao.PENDENTE

    # 3. Technician accepts the request
    accept_payload = {"observacao": "Iniciando reparo do teclado"}
    response = await tecnico_client.post(f"/solicitacoes-manutencao/{maint_req.id}/aceitar", data=accept_payload)
    assert response.status_code == 303
    
    await db_session.refresh(maint_req)
    await db_session.refresh(asset)
    assert maint_req.status == StatusSolicitacaoManutencao.EM_ANDAMENTO
    assert asset.status == AssetStatus.MANUTENCAO

    # 4. Technician completes maintenance (status becomes aguardando_entrega)
    complete_payload = {"observacao": "Teclado trocado com sucesso, pronto para retirada."}
    response = await tecnico_client.post(f"/solicitacoes-manutencao/{maint_req.id}/concluir", data=complete_payload)
    assert response.status_code == 303

    await db_session.refresh(maint_req)
    assert maint_req.status == StatusSolicitacaoManutencao.AGUARDANDO_ENTREGA

    # 5. Technician confirms delivery (simulating user QR validation)
    delivery_payload = {"observation": "Equipamento entregue em mãos para o colaborador."}
    response = await tecnico_client.post(f"/solicitacoes-manutencao/{maint_req.id}/confirmar-entrega", data=delivery_payload)
    assert response.status_code == 303

    await db_session.refresh(maint_req)
    await db_session.refresh(asset)
    assert maint_req.status == StatusSolicitacaoManutencao.ENTREGUE
    assert asset.status == AssetStatus.EM_USO
    assert asset.current_user_id == test_users["comum"].id

    # 6. User confirms receipt of the asset (concludes the request)
    response = await comum_client.post(f"/solicitacoes-manutencao/{maint_req.id}/confirmar-recebimento")
    assert response.status_code == 303

    await db_session.refresh(maint_req)
    await db_session.refresh(asset)
    assert maint_req.status == StatusSolicitacaoManutencao.CONCLUIDA
    assert asset.status == AssetStatus.EM_USO
    assert asset.current_user_id == test_users["comum"].id
