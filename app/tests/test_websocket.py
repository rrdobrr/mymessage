import asyncio
import websockets
import json
import aiohttp
import logging
from datetime import datetime
import pytest
from httpx import AsyncClient

from tests.conftest import (
    VALID_USER_DATA,
    INVALID_USER_DATA,
    VALID_LOGIN_DATA,
    INVALID_LOGIN_DATA,
    AUTH_USER_DATA
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

pytestmark = pytest.mark.asyncio

async def get_auth_token(client: AsyncClient):
    """Получение токена авторизации"""
    response = await client.post("/api/v1/auth/token", data=VALID_LOGIN_DATA)
    return response.json()['access_token']

async def connect_websocket(token: str, chat_id: int):
    """Вспомогательная функция для подключения к WebSocket"""
    uri = f"ws://localhost:8000/api/v1/messages/ws/chat/{chat_id}"
    async with websockets.connect(
        uri,
        additional_headers={"Authorization": f"Bearer {token}"}
    ) as websocket:
        # Ждем установления соединения
        await asyncio.sleep(0.5)
        
        # Отправляем тестовое сообщение в правильном формате
        test_message = {
            "text": "Test message",
            "message_type": "message"
        }
        await websocket.send(json.dumps(test_message))
        
        # Ждем ответа
        response = await websocket.recv()
        response_data = json.loads(response)
        
        assert response_data["type"] == "message"
        assert "text" in response_data
        assert "timestamp" in response_data
        assert "user_id" in response_data
        
        # Даем время на обработку сообщения
        await asyncio.sleep(0.5)
        
        return response_data

class TestWebSocket:
    """Тесты WebSocket"""
    
    @pytest.mark.asyncio
    async def test_websocket_connection(self, client: AsyncClient):
        """Тест подключения к WebSocket и обмена сообщениями"""
        token = await get_auth_token(client)
        assert token, "Не удалось получить токен авторизации"
        
        chat_id = 10
        try:
            response_data = await connect_websocket(token, chat_id)
            assert response_data["type"] == "message"
            assert "user_id" in response_data
            assert "timestamp" in response_data
        except Exception as e:
            pytest.fail(f"Ошибка при тестировании WebSocket: {str(e)}")

    @pytest.mark.asyncio
    async def test_websocket_reconnection(self, client: AsyncClient):
        """Тест переподключения к WebSocket"""
        token = await get_auth_token(client)
        assert token, "Не удалось получить токен авторизации"
        
        chat_id = 10
        try:
            # Первое подключение
            response_data1 = await connect_websocket(token, chat_id)
            assert response_data1["type"] == "message"
            
            # Даем время на закрытие первого соединения
            await asyncio.sleep(1)
            
            # Второе подключение
            response_data2 = await connect_websocket(token, chat_id)
            assert response_data2["type"] == "message"
        except Exception as e:
            pytest.fail(f"Ошибка при тестировании переподключения: {str(e)}")

