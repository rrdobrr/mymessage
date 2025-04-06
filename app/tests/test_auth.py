import pytest
from httpx import AsyncClient
from tests.conftest import (
    VALID_USER_DATA,
    INVALID_USER_DATA,
    VALID_LOGIN_DATA,
    INVALID_LOGIN_DATA,
    AUTH_USER_DATA
)

from src.core.logging import logger

pytestmark = pytest.mark.asyncio

class TestAuth:
    """Тесты аутентификации."""

    async def test_register_valid(self, client: AsyncClient):
        """Проверка успешной регистрации пользователя"""
        test_data = VALID_USER_DATA.copy()
        response = await client.post("/api/v1/auth/register", json=test_data)
        assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
        data = response.json()
        assert "id" in data, "ID пользователя отсутствует в ответе"
        assert data["email"] == test_data["email"], "Email не совпадает с отправленным"
        assert data["username"] == test_data["username"], "Username не совпадает"

    async def test_register_invalid(self, client: AsyncClient):
        """Проверка валидации данных при регистрации"""
        response = await client.post("/api/v1/auth/register", json=INVALID_USER_DATA)
        assert response.status_code == 422, f"Ожидался статус 422, получен {response.status_code}"
        data = response.json()
        assert "detail" in data, "Отсутствует описание ошибки"

    async def test_register_duplicate_email(self, client: AsyncClient):
        """Проверка регистрации с уже существующим email"""
        response = await client.post("/api/v1/auth/register", json=AUTH_USER_DATA)
        assert response.status_code == 409, f"Ожидался статус 409 при регистрации дубликата, получен {response.status_code}"

    async def test_login_valid(self, client: AsyncClient):
        """Проверка успешного входа в систему"""
        response = await client.post("/api/v1/auth/token", data=VALID_LOGIN_DATA)
        assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
        data = response.json()
        assert "access_token" in data, "Отсутствует access_token"
        assert "refresh_token" in data, "Отсутствует refresh_token"
        assert data["token_type"] == "bearer", "Неверный тип токена"

    async def test_login_invalid(self, client: AsyncClient):
        """Проверка входа с неверными данными"""
        response = await client.post("/api/v1/auth/token", data=INVALID_LOGIN_DATA)
        assert response.status_code == 401, f"Ожидался статус 401, получен {response.status_code}"

    async def test_refresh_token(self, client: AsyncClient):
        """Проверка обновления токена"""
        # Получаем токен через форму
        login_response = await client.post("/api/v1/auth/token", data=VALID_LOGIN_DATA)
        refresh_token = login_response.json().get("refresh_token")
        
        # Отправляем refresh token как JSON
        response = await client.post(
            "/api/v1/auth/refresh", 
            json={"refresh_token": refresh_token}
        )
        
        assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"
        data = response.json()
        assert "access_token" in data, "Отсутствует новый access_token"
        assert "refresh_token" in data, "Отсутствует новый refresh_token"
