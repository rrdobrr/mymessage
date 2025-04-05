import pytest
from httpx import AsyncClient
from tests.conftest import (
    VALID_USER_DATA,  # Используем существующие константы
    AUTH_USER_DATA,
    generate_random_email,
    generate_random_username
)

pytestmark = pytest.mark.asyncio

def generate_update_data():
    """Генерирует случайные данные для обновления профиля"""
    return {"username": generate_random_username()}

class TestUsers:
    """Тесты управления пользователями"""

    async def test_get_users_list(self, client: AsyncClient):
        """Тест получения списка пользователей"""
        # Используем данные из AUTH_USER_DATA для логина
        login_response = await client.post("/api/v1/auth/token", data={
            "username": AUTH_USER_DATA["email"],
            "password": AUTH_USER_DATA["password"]
        })
        tokens = login_response.json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        # Получаем список пользователей
        response = await client.get("/api/v1/users/list", headers=headers)
        assert response.status_code == 200, "Ошибка получения списка пользователей"
        users = response.json()
        assert isinstance(users, list), "Ответ должен быть списком"
        assert len(users) > 0, "Список пользователей пуст"
        assert "id" in users[0], "Отсутствует ID пользователя"

    async def test_get_user_by_id(self, client: AsyncClient):
        """Тест получения информации о конкретном пользователе"""
        login_response = await client.post("/api/v1/auth/token", data={
            "username": AUTH_USER_DATA["email"],
            "password": AUTH_USER_DATA["password"]
        })
        tokens = login_response.json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        user_id = 1
        response = await client.get(f"/api/v1/users/{user_id}", headers=headers)
        assert response.status_code == 200, "Успешное получение информации о пользователе"
        user_data = response.json()
        assert user_data["id"] == user_id, "ID пользователя не совпадает"

    async def test_update_profile(self, client: AsyncClient):
        """Тест обновления профиля пользователя"""
        # Логинимся
        login_response = await client.post("/api/v1/auth/token", data={
            "username": AUTH_USER_DATA["email"],
            "password": AUTH_USER_DATA["password"]
        })
        tokens = login_response.json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        # Получаем информацию о текущем пользователе
        me_response = await client.get("/api/v1/users/me", headers=headers)
        current_user = me_response.json()
        # Обновляем профиль
        update_data = generate_update_data()

        response = await client.patch(
            f"/api/v1/users/{current_user['id']}/update",
            headers=headers,
            json=update_data
        )
        assert response.status_code == 200, f"Ожидался статус 200, получен {response.status_code}"


    async def test_update_stranger_profile(self, client: AsyncClient):
        """Тест обновления чужого профиля"""
        # Логинимся
        login_response = await client.post("/api/v1/auth/token", data={
            "username": AUTH_USER_DATA["email"],
            "password": AUTH_USER_DATA["password"]
        })
        tokens = login_response.json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        # Получаем информацию о текущем пользователе
        me_response = await client.get("/api/v1/users/me", headers=headers)
        current_user_id = me_response.json()["id"]


        update_data = generate_update_data()
        user_id = current_user_id+1
        response = await client.patch(
            f"/api/v1/users/{user_id}/update",
            headers=headers,
            json=update_data
        )
        assert response.status_code == 403, "Должен быть запрещен доступ к чужому профилю"

    # async def test_delete_account(self, client: AsyncClient, test_user: dict):
        # """Тест удаления аккаунта"""
        # # Используем данные из VALID_USER_DATA для логина тестового пользователя
        # login_response = await client.post("/api/v1/auth/token", data={
        #     "username": VALID_USER_DATA["email"],
        #     "password": VALID_USER_DATA["password"]
        # })
        # tokens = login_response.json()
        # headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        # user_id = test_user["id"]
        # response = await client.delete(
        #     f"/api/v1/users/{user_id}/delete",
        #     headers=headers
        # )
        # assert response.status_code == 200, "Ошибка удаления аккаунта"

        # get_response = await client.get(
        #     f"/api/v1/users/{user_id}",
        #     headers=headers
        # )
        # assert get_response.status_code == 404, "Пользователь не был удален"
