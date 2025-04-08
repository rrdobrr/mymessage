import asyncio
import websockets
import json
import aiohttp
import logging
from datetime import datetime
import pytest
from httpx import AsyncClient
import uuid
from fastapi.testclient import TestClient
from main import app  # Импортируем основное приложение

from .logger_for_pytest import logger

from tests.conftest import (
    VALID_USER_DATA,
    INVALID_USER_DATA,
    VALID_LOGIN_DATA,
    INVALID_LOGIN_DATA,
    AUTH_USER_DATA,
    ADDITIONAL_TEST_USER_DATA,
    ADDITIONAL_TEST_USER_DATA_2
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

pytestmark = pytest.mark.asyncio

# Дополнительные тестовые пользователи




async def get_auth_token(client: AsyncClient, data: dict = VALID_LOGIN_DATA):
    """Получение токена авторизации"""
    response = await client.post("/api/v1/auth/token", data=data)
    return response.json()['access_token']

async def connect_websocket(token: str, chat_id: int) -> websockets.WebSocketClientProtocol:
    """Вспомогательная функция для подключения к WebSocket"""
    uri = f"ws://localhost:8000/api/v1/websocket/chat/{chat_id}"
    try:
        websocket = await websockets.connect(
            uri,
            additional_headers={"Authorization": f"Bearer {token}"},
            open_timeout=5,
            close_timeout=5
        )
        return websocket
    except Exception as e:
        logger.error(f"WebSocket connection failed: {str(e)}")
        raise

async def send_and_receive_message(websocket: websockets.WebSocketClientProtocol, chat_id: int) -> dict:
    """Отправка сообщения и получение ответа"""
    try:
        # Отправляем сообщение
        message = {
            "message_type": "new_message",
            "text": "Test message",
            "idempotency_key": generate_idempotency_key(),
            "chat_id": chat_id
        }
        await websocket.send(json.dumps(message))
        
        # Ждем ответ с таймаутом
        response = await asyncio.wait_for(websocket.recv(), timeout=5)
        return json.loads(response)
        
    except asyncio.TimeoutError:
        logger.error("Timeout waiting for WebSocket response")
        raise
    except Exception as e:
        logger.error(f"Error in message exchange: {str(e)}")
        raise

def generate_idempotency_key() -> str:
    """Генерирует уникальный idempotency ключ"""
    timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
    unique_id = str(uuid.uuid4())
    return f"{timestamp}-{unique_id}"

async def wait_for_type(ws, field: str, expected_type: str, timeout: float = 5.0):
    """Получение сообщения с ожидаемым типом"""
    async def _receive():
        while True:
            msg = json.loads(await ws.recv())
            if msg.get(field) == expected_type:
                return msg
    return await asyncio.wait_for(_receive(), timeout)



class TestWebSocket:
    """Тесты WebSocket"""
        

    @pytest.mark.skipif(False, reason="Отключено для отладки")
    @pytest.mark.asyncio
    async def test_websocket_connection(self, client: AsyncClient):
        """Тест подключения к WebSocket и обмена сообщениями"""
        token = await get_auth_token(client)
        assert token, "Не удалось получить токен авторизации"
        
        chat_id = 1
        try:
            async with await connect_websocket(token, chat_id) as websocket:
                response_data = await send_and_receive_message(websocket, chat_id)
                
                # Проверяем ответ
                assert response_data is not None, "No response received"
                assert response_data["response_type"] == "new_message", f"Unexpected response type: {response_data.get('response_type')}"
                assert "message_id" in response_data, "Response missing message_id"
                assert "sender_id" in response_data, "Response missing sender_id"
                assert "text" in response_data, "Response missing text"
                assert response_data["text"] == "Test message", "Message text mismatch"
                
                # Даем время на корректное закрытие соединения
                await asyncio.sleep(0.2)
                
        except Exception as e:
            logger.error(f"Test failed: {str(e)}", exc_info=True)
            raise

    @pytest.mark.skipif(False, reason="Отключено для отладки")   
    @pytest.mark.asyncio
    async def test_websocket_reconnection(self, client: AsyncClient):
        """Тест переподключения к WebSocket"""
        token = await get_auth_token(client)
        assert token, "Не удалось получить токен авторизации"
        
        chat_id = 1
        try:
            # Первое подключение и отправка сообщения
            async with await connect_websocket(token, chat_id) as websocket1:
                response_data1 = await send_and_receive_message(websocket1, chat_id)
                assert response_data1["response_type"] == "new_message"
            
            await asyncio.sleep(0.1)
            
            # Второе подключение и отправка сообщения
            async with await connect_websocket(token, chat_id) as websocket2:
                response_data2 = await send_and_receive_message(websocket2, chat_id)
                assert response_data2["response_type"] == "new_message"
                
        except Exception as e:
            logger.error(f"Ошибка при тестировании переподключения: {str(e)}")
            raise

    @pytest.mark.skipif(False, reason="Отключено для отладки")  
    @pytest.mark.asyncio
    async def test_idempotency(self, client: AsyncClient):
        """Тест идемпотентности отправки сообщений"""
        token = await get_auth_token(client)
        chat_id = 1
        idempotency_key = generate_idempotency_key()
        
        async with websockets.connect(
            f"ws://localhost:8000/api/v1/websocket/chat/{chat_id}",
            additional_headers={"Authorization": f"Bearer {token}"}
        ) as websocket:
            # Отправляем сообщение с idempotency key
            test_message = {
                "text": "Test idempotency",
                "message_type": "new_message",
                "idempotency_key": idempotency_key,
                "chat_id": chat_id
            }
            
            # Отправляем одно и то же сообщение дважды
            await websocket.send(json.dumps(test_message))
            await asyncio.sleep(0.1)  # Даем время на обработку первого сообщения
            await websocket.send(json.dumps(test_message))
            
            # Получаем ответы
            response1 = await websocket.recv()
            response2 = await websocket.recv()
            
            data1 = json.loads(response1)
            data2 = json.loads(response2)
            
            # Проверяем, что сообщения идентичны
            assert data1["response_type"] == "new_message"
            assert data2["response_type"] == "new_message"
            assert data1["message_id"] == data2["message_id"]
            assert data1["text"] == data2["text"]
            assert data1["chat_id"] == data2["chat_id"]

    @pytest.mark.skipif(False, reason="Отключено для отладки")
    @pytest.mark.asyncio
    async def test_message_read_status(self, client: AsyncClient):
        """Тест статуса прочтения сообщения"""
        token1 = await get_auth_token(client)
        chat_id = 1
        
        async with websockets.connect(
            f"ws://localhost:8000/api/v1/websocket/chat/{chat_id}",
            additional_headers={"Authorization": f"Bearer {token1}"}
        ) as ws1:
            # Отправляем сообщение
            test_message = {
                "text": "Test read status",
                "message_type": "new_message",
                "idempotency_key": generate_idempotency_key(),
                "chat_id": chat_id  # Явно указываем chat_id
            }
            await ws1.send(json.dumps(test_message))
            
            # Получаем ответ о создании сообщения
            message_response = await ws1.recv()
            message_data = json.loads(message_response)
            logger.info(f"Message data received: {message_data}")
            message_id = message_data["message_id"]
            
            # Отправляем статус прочтения
            read_status = {
                "message_type": "read_status",
                "message_id": message_id,
                "chat_id": chat_id  # Добавляем chat_id в статус прочтения
            }
            await ws1.send(json.dumps(read_status))
            
            # Получаем подтверждение о прочтении
            read_notification = await ws1.recv()
            read_data = json.loads(read_notification)
            logger.info(f"Received read status response: {read_data}")  # Добавляем логирование

            # Проверяем корректность ответа
            assert read_data["response_type"] == "read_status"
            assert read_data["message_id"] == message_id
            assert read_data["chat_id"] == chat_id
            assert len(read_data["read_by"]) > 0
            assert "read_by" in read_data

    @pytest.mark.skipif(False, reason="Отключено для отладки")
    @pytest.mark.asyncio
    async def test_websocket_two_users_message_flow(self, client: AsyncClient):
        """Тест обмена сообщениями между двумя пользователями"""
        # Получаем токены для пользователей


        token1 = await get_auth_token(client, data=VALID_LOGIN_DATA)
        token2 = await get_auth_token(client, data=ADDITIONAL_TEST_USER_DATA)
        
        chat_id = 1 

        # Подключаемся к WebSocket
        ws1 = await connect_websocket(token1, chat_id)
        ws2 = await connect_websocket(token2, chat_id)
        
        try:
            # Отправляем сообщение от первого пользователя
            test_message = "Привет, это тестовое сообщение!"
            await ws1.send(json.dumps({
                "message_type": "new_message",
                "chat_id": chat_id,
                "text": test_message,
                "idempotency_key": generate_idempotency_key()

            }))
            logger.info("User 1 sent message")



            # Оба пользователя получат NewMessageResponse
            response1 = await wait_for_type(ws1, "response_type", "new_message")
            logger.info(f"User 1 received response after sending: {response1}")
            assert response1["response_type"] == "new_message"  # Тип ответа
            assert response1["text"] == test_message



            response2 = json.loads(await ws2.recv())
            logger.info(f"User 2 received message: {response2}")

            assert response2["message_type"] == "new_message"  # Тот же тип для всех
            assert response2["text"] == test_message
            
            logger.info(f"Чек 1")
            # Отправляем ответное сообщение
            reply_message = "Получил сообщение!"
            await ws2.send(json.dumps({
                "message_type": "new_message",
                "chat_id": chat_id,
                "text": reply_message,
                "idempotency_key": generate_idempotency_key()

            }))
            logger.info(f"Чек 2")
            message2 = json.loads(await ws2.recv())

            logger.info(f"User 2 sent message: {message2}")
            logger.info(f"Чек 3")
            # Получаем ответ первым пользователем
            response3 = json.loads(await ws1.recv())
            logger.info(f"User 1 received new message notification: {response3}")
            assert response3["message_type"] == "new_message"
            assert response3["text"] == reply_message

            await ws1.send(json.dumps({
                "message_type": "read_status",
                "chat_id": chat_id,
                "message_id": message2["message_id"]
            }))
            logger.info("User 1 sending read status")
            # Отправляем статус прочтения
            await asyncio.sleep(0.5)
            read_status = json.loads(await ws2.recv())
            # Даем время на обработку статуса прочтения

            
            logger.info(f"User 2 received read status: {read_status}")
            assert read_status["message_type"] == "read_status"
            assert read_status["message_id"] == message2["message_id"]
        
        finally:
            # Закрываем соединения
            await ws1.close()
            await ws2.close()

    @pytest.mark.skipif(False, reason="Отключено для отладки")
    @pytest.mark.asyncio
    async def test_websocket_three_users_message_flow(self, client: AsyncClient):
        """Тест обмена сообщениями между тремя пользователями"""
        # Получаем токены для всех пользователей
        token1 = await get_auth_token(client, VALID_LOGIN_DATA)
        token2 = await get_auth_token(client, ADDITIONAL_TEST_USER_DATA)
        token3 = await get_auth_token(client, ADDITIONAL_TEST_USER_DATA_2)
        
        chat_id = 1
        
        # Подключаемся к WebSocket
        ws1 = await connect_websocket(token1, chat_id)
        ws2 = await connect_websocket(token2, chat_id)
        ws3 = await connect_websocket(token3, chat_id)
        
        try:
            # Первый пользователь отправляет сообщение
            initial_message = "Привет всем в групповом чате!"
            await ws1.send(json.dumps({
                "message_type": "new_message",
                "chat_id": chat_id,
                "text": initial_message,
                "idempotency_key": generate_idempotency_key()
            }))
            
            # Все получают сообщение
            response1 = await wait_for_type(ws1, "response_type", "new_message")
            logger.info(f"User 1 received response after sending: {response1}")
            assert response1["response_type"] == "new_message"
            assert response1["text"] == initial_message
            
            response2 = await wait_for_type(ws2, "message_type", "new_message")
            logger.info(f"User 2 received message: {response2}")
            assert response2["message_type"] == "new_message"
            assert response2["text"] == initial_message
            
            response3 = json.loads(await ws3.recv())
            logger.info(f"User 3 received message: {response3}")
            assert response3["message_type"] == "new_message"
            assert response3["text"] == initial_message
            
            # Второй пользователь отвечает
            reply1 = "Привет! Как дела?"
            await ws2.send(json.dumps({
                "message_type": "new_message",
                "chat_id": chat_id,
                "text": reply1,
                "idempotency_key": generate_idempotency_key()
            }))
            
            message2 = json.loads(await ws2.recv())
            logger.info(f"User 2 sent message: {message2}")
            
            # Первый и третий получают ответ
            response1 = json.loads(await ws1.recv())
            logger.info(f"User 1 received response after sending: {response1}")
            assert response1["message_type"] == "new_message"
            assert response1["text"] == reply1
            
            response3 = json.loads(await ws3.recv())
            logger.info(f"User 3 received response after sending: {response3}")
            assert response3["message_type"] == "new_message"
            assert response3["text"] == reply1
            
            # Отправляем статусы прочтения
            for ws in [ws1, ws3]:
                await ws.send(json.dumps({
                    "message_type": "read_status",
                    "chat_id": chat_id,
                    "message_id": message2["message_id"]
                }))
                logger.info("Sending read status")
            
            # Все получают обновления статусов
            await asyncio.sleep(0.1)  # Даем время на обработку
            for _ in range(2):  # Ожидаем два статуса прочтения
                status_update = json.loads(await ws2.recv())
                logger.info(f"Received status update: {status_update}")
                assert status_update["message_type"] == "read_status"
                assert status_update["message_id"] == message2["message_id"]
            
        finally:
            # Закрываем соединения
            await ws1.close()
            await ws2.close()
            await ws3.close()

    @pytest.mark.skipif(False, reason="Отключено для отладки")
    @pytest.mark.asyncio
    async def test_multiple_devices_connection(self, client: AsyncClient):
        """Тест подключения одного пользователя с нескольких устройств"""
        # Получаем токен для пользователя
        token = await get_auth_token(client, VALID_LOGIN_DATA)
        chat_id = 1

        # Создаем три подключения, имитируя разные устройства
        ws1 = await connect_websocket(token, chat_id)
        ws2 = await connect_websocket(token, chat_id)
        ws3 = await connect_websocket(token, chat_id)

        try:
            # Отправляем сообщение с первого "устройства"
            test_message = "Сообщение с первого устройства"
            await ws1.send(json.dumps({
                "message_type": "new_message",
                "chat_id": chat_id,
                "text": test_message,
                "idempotency_key": generate_idempotency_key()
            }))

            # Получаем ответ на первом устройстве
            response1 = json.loads(await ws1.recv())
            logger.info(f"Device 1 received response after sending: {response1}")
            assert response1["response_type"] == "new_message"
            assert response1["text"] == test_message

            # Отправляем сообщение со второго "устройства"
            second_message = "Сообщение со второго устройства"
            await ws2.send(json.dumps({
                "message_type": "new_message",
                "chat_id": chat_id,
                "text": second_message,
                "idempotency_key": generate_idempotency_key()
            }))

            # Получаем ответ на втором устройстве
            response2 = json.loads(await ws2.recv())
            logger.info(f"Device 2 received response after sending: {response2}")
            assert response2["response_type"] == "new_message"
            assert response2["text"] == second_message

            # Отправляем статус прочтения с третьего устройства
            await ws3.send(json.dumps({
                "message_type": "read_status",
                "chat_id": chat_id,
                "message_id": response2["message_id"]
            }))

            # Проверяем, что статус прочтения получен на всех устройствах
            await asyncio.sleep(0.1)  # Даем время на обработку
            read_status = json.loads(await ws3.recv())
            logger.info(f"Device 3 received confirmation of read status: {read_status}")
            assert read_status["response_type"] == "read_status"
            assert read_status["message_id"] == response2["message_id"]

        finally:
            # Закрываем все соединения
            for ws in [ws1, ws2, ws3]:
                await ws.close()

    @pytest.mark.skipif(False, reason="Отключено для отладки")
    @pytest.mark.asyncio
    async def test_user_online_status_notifications(self, client: AsyncClient):
        """Тест уведомлений о статусе пользователей (онлайн/офлайн)"""
        # Получаем токены для двух пользователей
        token1 = await get_auth_token(client, VALID_LOGIN_DATA)
        token2 = await get_auth_token(client, ADDITIONAL_TEST_USER_DATA)
        chat_id = 1

        # Подключаем первого пользователя
        ws1 = await connect_websocket(token1, chat_id)
        
        try:
            # Ждем немного, чтобы первый пользователь получил статус "онлайн"
            await asyncio.sleep(0.1)
            
            # Подключаем второго пользователя
            ws2 = await connect_websocket(token2, chat_id)

            logger.info("User 2 connected")
            # Первый пользователь должен получить уведомление о подключении второго
            status_notification = json.loads(await ws1.recv())
            logger.info(f"User 1 received status notification: {status_notification}")
            assert status_notification["message_type"] == "user_status"
            assert status_notification["status"] == "online"
            
            # Отключаем второго пользователя
            await ws2.close()
            
            # Первый пользователь должен получить уведомление об отключении второго
            offline_notification = json.loads(await ws1.recv())
            logger.info(f"User 1 received offline notification: {offline_notification}")
            assert offline_notification["message_type"] == "user_status"
            assert offline_notification["status"] == "offline"

            # Подключаем второго пользователя снова
            ws2 = await connect_websocket(token2, chat_id)
            
            # Проверяем получение уведомления о повторном подключении
            online_again_notification = json.loads(await ws1.recv())
            logger.info(f"User 1 received online notification: {online_again_notification}")
            assert online_again_notification["message_type"] == "user_status"
            assert online_again_notification["status"] == "online"

        finally:
            # Закрываем все соединения
            if 'ws1' in locals():
                await ws1.close()
            if 'ws2' in locals():
                await ws2.close()

