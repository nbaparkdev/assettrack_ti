import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import user as user_crud
from app.crud.system_settings import system_settings
from app.schemas.user import UserCreate


@pytest.fixture
async def common_user(db_session: AsyncSession):
    user_in = UserCreate(
        nome="Common User",
        email="common@example.com",
        password="password123",
        role="usuario_comum",
        is_active=True
    )
    user = await user_crud.user.create(db_session, obj_in=user_in)
    return user

@pytest.fixture
async def rh_user(db_session: AsyncSession):
    user_in = UserCreate(
        nome="RH User",
        email="rh@example.com",
        password="password123",
        role="rh",
        is_active=True
    )
    user = await user_crud.user.create(db_session, obj_in=user_in)
    return user

@pytest.fixture
async def common_client(client: AsyncClient, common_user):
    await client.post("/login", data={
        "email": "common@example.com", 
        "password": "password123"
    })
    return client

@pytest.fixture
async def rh_client(client: AsyncClient, rh_user):
    await client.post("/login", data={
        "email": "rh@example.com", 
        "password": "password123"
    })
    return client

@pytest.mark.asyncio
async def test_dashboard_custom_links_for_common_user(common_client: AsyncClient, db_session: AsyncSession):
    # 1. Configure custom links in system settings
    custom_links_text = "Wiki Corporativa | https://wiki.empresa.com\nPolíticas de TI | https://intranet.empresa.com"
    await system_settings.set_setting(
        db=db_session,
        setting_key="custom_links_comum",
        setting_value=custom_links_text
    )
    await db_session.commit()

    # 2. Get dashboard page
    response = await common_client.get("/")
    assert response.status_code == 200
    assert "Wiki Corporativa" in response.text
    assert "https://wiki.empresa.com" in response.text
    assert "Políticas de TI" in response.text
    assert "https://intranet.empresa.com" in response.text

@pytest.mark.asyncio
async def test_dashboard_custom_links_for_rh_user(rh_client: AsyncClient, db_session: AsyncSession):
    # 1. Configure custom links in system settings
    custom_links_text = "Portal RH | https://rh.empresa.com"
    await system_settings.set_setting(
        db=db_session,
        setting_key="custom_links_comum",
        setting_value=custom_links_text
    )
    await db_session.commit()

    # 2. Get dashboard page as RH user
    response = await rh_client.get("/")
    assert response.status_code == 200
    assert "Portal RH" in response.text
    assert "https://rh.empresa.com" in response.text
