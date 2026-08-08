import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.crud import user as user_crud
from app.schemas.user import UserCreate
from app.models.emergency_alert import EmergencyAlert

@pytest.mark.asyncio
async def test_send_emergency_alert_success(client: AsyncClient, db_session: AsyncSession):
    # 1. Arrange: Create common user
    user_in = UserCreate(
        nome="Carlos Operador",
        email="carlos@example.com",
        password="password123",
        cargo="Operador de TI",
        role="usuario_comum",
        is_active=True
    )
    user = await user_crud.user.create(db_session, obj_in=user_in)

    # Login to set access_token cookie
    login_resp = await client.post("/login", data={"email": "carlos@example.com", "password": "password123"})
    assert login_resp.status_code == 302

    # 2. Act: Send emergency alert
    payload = {"motivo": "Computador reiniciando sozinho em loop constante!"}
    response = await client.post("/emergencia/alertar", data=payload)

    # 3. Assert
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"

    # Verify DB record
    res = await db_session.execute(select(EmergencyAlert).filter(EmergencyAlert.usuario_id == user.id))
    alerts = res.scalars().all()
    assert len(alerts) == 1
    alert = alerts[0]
    assert alert.usuario_nome == "Carlos Operador"
    assert alert.motivo == "Computador reiniciando sozinho em loop constante!"
    assert alert.setor_nome == "Operador de TI"

@pytest.mark.asyncio
async def test_send_emergency_alert_blank_reason(client: AsyncClient, db_session: AsyncSession):
    # Arrange
    user_in = UserCreate(
        nome="Ana Maria",
        email="ana@example.com",
        password="password123",
        role="usuario_comum",
        is_active=True
    )
    await user_crud.user.create(db_session, obj_in=user_in)
    await client.post("/login", data={"email": "ana@example.com", "password": "password123"})

    # Act: Send empty reason
    response = await client.post("/emergencia/alertar", data={"motivo": "   "})
    assert response.status_code == 400
    assert "motivo" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_emergency_history_and_atender(client: AsyncClient, db_session: AsyncSession):
    # 1. Arrange: Create common user and admin user
    user_in = UserCreate(
        nome="João Silva",
        email="joao@example.com",
        password="password123",
        role="usuario_comum",
        is_active=True
    )
    admin_in = UserCreate(
        nome="Admin Suporte",
        email="adminsup@example.com",
        password="password123",
        role="admin",
        is_active=True
    )
    u_comum = await user_crud.user.create(db_session, obj_in=user_in)
    u_admin = await user_crud.user.create(db_session, obj_in=admin_in)

    # User triggers alert
    alert = EmergencyAlert(
        usuario_id=u_comum.id,
        usuario_nome=u_comum.nome,
        setor_nome="TI",
        ativo_nome="Notebook Dell",
        motivo="Servidor inacessível",
        atendido=False
    )
    db_session.add(alert)
    await db_session.commit()
    await db_session.refresh(alert)

    # 2. Login as admin
    await client.post("/login", data={"email": "adminsup@example.com", "password": "password123"})

    # 3. Check history endpoint
    resp_hist = await client.get("/emergencia/historico")
    assert resp_hist.status_code == 200
    data_hist = resp_hist.json()
    assert data_hist["total"] >= 1
    assert data_hist["pendentes"] >= 1

    # 4. Mark as atendido
    resp_atender = await client.post(f"/emergencia/{alert.id}/atender")
    assert resp_atender.status_code == 200
    assert resp_atender.json()["status"] == "success"

    # Verify DB
    await db_session.refresh(alert)
    assert alert.atendido is True
    assert alert.atendido_por_id == u_admin.id
