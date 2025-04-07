import pytest
from httpx import AsyncClient
from .conftest import AUTH_USER_DATA
from .logger_for_pytest import logger

pytestmark = pytest.mark.asyncio  # Добавляем маркер для всех тестов в модуле

async def get_existing_chat(client: AsyncClient, headers: dict) -> int:
    """Вспомогательная функция для получения ID существующего чата пользователя"""
    response = await client.get("/api/v1/chats/list", headers=headers)
    chats = response.json()
    if not chats:
        raise ValueError("У пользователя нет доступных чатов")
    return chats[0]["id"]  # Возвращаем ID первого найденного чата

class TestMessages:
    """Тесты для работы с сообщениями"""

    async def test_send_message(self, client: AsyncClient):
        """Тест отправки сообщения в чат"""
        # Логинимся
        login_response = await client.post("/api/v1/auth/token", data={
            "username": AUTH_USER_DATA["email"],
            "password": AUTH_USER_DATA["password"]
        })
        tokens = login_response.json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        
        # Получаем ID текущего пользователя
        me_response = await client.get("/api/v1/users/me", headers=headers)
        user_id = me_response.json()["id"]
        
        # Получаем существующий чат
        chat_id = await get_existing_chat(client, headers)
        
        # Отправляем сообщение
        message_data = {
            "text": "Test message",
            "chat_id": chat_id,
            "sender_id": user_id
        }
        response = await client.post("/api/v1/messages/create", headers=headers, json=message_data)
        logger.info(f"Response received: {response}")
        # Если ошибка, выведем детали
        if response.status_code != 201:
            error_detail = response.json()
            logger.info(f"Error details: {error_detail}")
            
        assert response.status_code == 201, f"Ожидался статус 201, получен {response.status_code}"
        message = response.json()
        assert message["text"] == message_data["text"]
        assert message["chat_id"] == chat_id
        assert message["sender_id"] == user_id 