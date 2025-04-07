import asyncio
import websockets
import json
import aiohttp
import logging
from datetime import datetime
import pytest
from httpx import AsyncClient
import uuid
from src.features.websocket.schemas import WebSocketMessageType

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
    uri = f"ws://localhost:8000/api/v1/websocket/chat/{chat_id}"
    try:
        async with websockets.connect(
            uri,
            additional_headers={"Authorization": f"Bearer {token}"},
            open_timeout=5,
            close_timeout=5
        ) as websocket:
            message = {
                "message_type": WebSocketMessageType.NEW_MESSAGE,
                "text": "Test message",
                "idempotency_key": generate_idempotency_key(),
                "chat_id": chat_id
            }
            await websocket.send(json.dumps(message))
            
            response = await asyncio.wait_for(websocket.recv(), timeout=2)
            response_data = json.loads(response)
            return response_data
                
    except Exception as e:
        logger.error(f"WebSocket connection failed: {str(e)}")
        pytest.fail(f"WebSocket connection failed: {str(e)}")

def generate_idempotency_key() -> str:
    """Генерирует уникальный idempotency ключ"""
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    unique_id = str(uuid.uuid4())
    return f"{timestamp}-{unique_id}"

class TestWebSocket:
    """Тесты WebSocket"""
        

    @pytest.mark.skipif(False, reason="Отключено для отладки")
    @pytest.mark.asyncio
    async def test_websocket_connection(self, client: AsyncClient):
        """Тест подключения к WebSocket и обмена сообщениями"""
        token = await get_auth_token(client)
        assert token, "Не удалось получить токен авторизации"
        
        chat_id = 10  # Используем фиксированный chat_id для теста
        try:
            response_data = await connect_websocket(token, chat_id)
            
            # Проверяем ответ
            assert response_data is not None, "No response received"
            assert response_data["type"] == WebSocketMessageType.NEW_MESSAGE, f"Unexpected response type: {response_data.get('type')}"
            assert "message_id" in response_data, "Response missing message_id"
            assert "sender_id" in response_data, "Response missing sender_id"
            assert "text" in response_data, "Response missing text"
            assert response_data["text"] == "Test message", "Message text mismatch"
            
        except Exception as e:
            logger.error(f"Test failed: {str(e)}", exc_info=True)
            pytest.fail(f"Ошибка при тестировании WebSocket: {str(e)}")

    @pytest.mark.skipif(False, reason="Отключено для отладки")   
    @pytest.mark.asyncio
    async def test_websocket_reconnection(self, client: AsyncClient):
        """Тест переподключения к WebSocket"""
        token = await get_auth_token(client)
        assert token, "Не удалось получить токен авторизации"
        
        chat_id = 10
        try:
            # Первое подключение
            response_data1 = await connect_websocket(token, chat_id)
            assert response_data1["type"] == WebSocketMessageType.NEW_MESSAGE
            
            await asyncio.sleep(0.1)
            
            # Второе подключение
            response_data2 = await connect_websocket(token, chat_id)
            assert response_data2["type"] == WebSocketMessageType.NEW_MESSAGE
        except Exception as e:
            pytest.fail(f"Ошибка при тестировании переподключения: {str(e)}")

    @pytest.mark.skipif(False, reason="Отключено для отладки")  
    @pytest.mark.asyncio
    async def test_idempotency(self, client: AsyncClient):
        """Тест идемпотентности отправки сообщений"""
        token = await get_auth_token(client)
        chat_id = 10
        idempotency_key = generate_idempotency_key()
        
        async with websockets.connect(
            f"ws://localhost:8000/api/v1/websocket/chat/{chat_id}",
            additional_headers={"Authorization": f"Bearer {token}"}
        ) as websocket:
            # Отправляем сообщение с idempotency key
            test_message = {
                "text": "Test idempotency",
                "message_type": WebSocketMessageType.NEW_MESSAGE,
                "idempotency_key": idempotency_key
            }
            
            # Отправляем одно и то же сообщение дважды
            await websocket.send(json.dumps(test_message))
            await websocket.send(json.dumps(test_message))
            
            # Получаем ответы
            response1 = await websocket.recv()
            response2 = await websocket.recv()
            
            print(f"СМОТРИМ НА ОТВЕТ 1 : {response1}")
            print(f"СМОТРИМ НА ОТВЕТ 2 : {response2}")

            data1 = json.loads(response1)
            data2 = json.loads(response2)
            
            # Проверяем, что ID сообщений одинаковые
            assert data1["message_id"] == data2["message_id"]

    @pytest.mark.asyncio
    async def test_message_read_status(self, client: AsyncClient):
        """Тест статуса прочтения сообщения"""
        token1 = await get_auth_token(client)
        chat_id = 10
        
        async with websockets.connect(
            f"ws://localhost:8000/api/v1/websocket/chat/{chat_id}",
            additional_headers={"Authorization": f"Bearer {token1}"}
        ) as ws1:
            # Отправляем сообщение
            test_message = {
                "text": "Test read status",
                "message_type": WebSocketMessageType.NEW_MESSAGE,
                "idempotency_key": generate_idempotency_key(),
                "chat_id": chat_id  # Явно указываем chat_id
            }
            await ws1.send(json.dumps(test_message))
            
            # Получаем ответ о создании сообщения
            message_response = await ws1.recv()
            message_data = json.loads(message_response)
            print(f"СМОТРИМ НА ОТВЕТ: {message_data}")
            print(f"СМОТРИМ НА ОТВЕТ: {message_data}")
            print(f"СМОТРИМ НА ОТВЕТ: {message_data}")
            print(f"СМОТРИМ НА ОТВЕТ: {message_data}")
            message_id = message_data["message_id"]
            
            # Отправляем статус прочтения
            read_status = {
                "message_type": WebSocketMessageType.READ_STATUS,
                "message_id": message_id,
                "chat_id": chat_id  # Добавляем chat_id в статус прочтения
            }
            await ws1.send(json.dumps(read_status))
            
            # Получаем подтверждение о прочтении
            read_notification = await ws1.recv()
            read_data = json.loads(read_notification)
            logger.info(f"Received read status response: {read_data}")  # Добавляем логирование

            # Проверяем корректность ответа
            assert read_data["type"] == WebSocketMessageType.READ_STATUS
            assert read_data["message_id"] == message_id
            assert read_data["chat_id"] == chat_id
            assert read_data["is_read"] is True
            assert "read_by" in read_data

    async def test_websocket_message_flow(self, client: AsyncClient):
        """Тест полного цикла обмена сообщениями"""
        # Получаем токен и подключаемся к чату
        token = await get_auth_token(client)
        chat_id = 1  # Предполагаем, что чат существует
        
        # Отправляем и получаем сообщение
        response = await connect_websocket(token, chat_id)
        
        # Проверяем структуру ответа
        assert response["message_type"] == WebSocketMessageType.NEW_MESSAGE
        assert "message_id" in response
        assert response["chat_id"] == chat_id
        assert "sender_id" in response
        assert "text" in response
        assert "timestamp" in response
        assert "is_read" in response
        assert "read_by" in response

