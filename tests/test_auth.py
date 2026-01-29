import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.crud import user as user_crud

@pytest.mark.asyncio
async def test_register_user_success(client: AsyncClient, db_session: AsyncSession):
    # Act
    payload = {
        "nome": "Test User",
        "email": "test@example.com",
        "password": "strongpassword",
        "matricula": "12345",
        "cargo": "Analyst"
    }
    response = await client.post("/register", data=payload)
    
    # Assert
    assert response.status_code == 302 # Redirects to login
    assert response.headers["location"] == "/login"
    
    # Verify DB
    user = await user_crud.user.get_by_email(db_session, email="test@example.com")
    assert user is not None
    assert user.nome == "Test User"
    assert user.is_active is False
    assert user_crud.user.verify_password("strongpassword", user.hashed_password)

@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, db_session: AsyncSession):
    # Arrange
    payload = {
        "nome": "Test User",
        "email": "existing@example.com",
        "password": "password",
        "matricula": "12345",
        "cargo": "Analyst"
    }
    await client.post("/register", data=payload)
    
    # Act
    response = await client.post("/register", data=payload)
    
    # Assert
    assert response.status_code == 200 # Returns template with error
    assert "Email já cadastrado" in response.text

@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, db_session: AsyncSession):
    # Arrange
    from app.schemas.user import UserCreate
    user_in = UserCreate(
        nome="Login User",
        email="login@example.com",
        password="loginpass",
        role="admin",
        is_active=True
    )
    await user_crud.user.create(db_session, obj_in=user_in)
    
    # Act
    payload = {
        "email": "login@example.com",
        "password": "loginpass"
    }
    response = await client.post("/login", data=payload)
    
    # Assert
    assert response.status_code == 302
    assert response.headers["location"] == "/"
    assert "access_token" in response.cookies

@pytest.mark.asyncio
async def test_login_failure(client: AsyncClient):
    # Act
    payload = {
        "email": "wrong@example.com",
        "password": "wrongpassword"
    }
    response = await client.post("/login", data=payload)
    
    # Assert
    assert response.status_code == 200
    assert "Email ou senha incorretos" in response.text
