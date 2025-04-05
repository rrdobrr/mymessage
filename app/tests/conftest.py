import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
import random
import string

from src.main import app
from src.core.db import engine, Base, AsyncSessionFactory, get_db


@pytest_asyncio.fixture(scope="session")
async def setup_db():
    """Настраивает базу данных для тестов"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

@pytest_asyncio.fixture
async def session():
    """Создает сессию для теста"""
    async with AsyncSessionFactory() as session:
        yield session

# Тестовые данные для аутентификации
def generate_random_email():
    """Генерирует случайный email для тестов"""
    random_string = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    return f"test_{random_string}@example.com"

def generate_random_username():
    """Генерирует случайный username для тестов"""
    random_username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    return random_username

AUTH_USER_DATA = {
    "email": "test@test.com",
    "username": "testuser",
    "password": "testotest"
}

VALID_USER_DATA = {
    "email": generate_random_email(),
    "username": generate_random_username(),
    "password": "testpass123"
}

INVALID_USER_DATA = {
    "email": "invalid-email",
    "username": "t",
    "password": "short"
}

VALID_LOGIN_DATA = {
    "username": "test@test.com",
    "password": "testotest"
}

INVALID_LOGIN_DATA = {
    "username": "wrong@example.com",
    "password": "wrongpass"
}

@pytest_asyncio.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="function")
async def session():
    """Создает новую сессию для каждого теста"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    async with sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )() as session:
        yield session
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

async def override_get_db():
    """Переопределяет функцию получения сессии БД для тестов"""
    async with AsyncSessionFactory() as session:
        yield session

@pytest_asyncio.fixture
async def client() -> AsyncClient:
    """Создает тестовый клиент"""
    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()

@pytest_asyncio.fixture
async def auth_user(client):
    """Создает пользователя для тестов авторизации"""
    response = await client.post("/api/v1/auth/register", json=AUTH_USER_DATA)
    assert response.status_code == 200
    return response.json()

@pytest_asyncio.fixture
async def test_user(client):
    """Создает тестового пользователя со случайным email"""
    user_data = VALID_USER_DATA.copy()
    user_data["email"] = generate_random_email()
    response = await client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 200
    return response.json()