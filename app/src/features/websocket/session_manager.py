from fastapi import WebSocket
from typing import Dict, Union, Any
from src.core.logging import logger
import json
from datetime import datetime
from .schemas import (
    BaseWSResponse,
    NewMessageResponse,
    ReadStatusResponse,
    UserStatusResponse
)
from pydantic import parse_obj_as
from collections import defaultdict
from typing import Literal


from .utils import DateTimeEncoder


class WebSocketSessionManager:
    def __init__(self):
        # Структура: {chat_id: {user_id: websocket}}
        self.active_connections: Dict[int, Dict[int, WebSocket]] = defaultdict(dict)

    async def connect(self, websocket: WebSocket, chat_id: int, user_id: int):
        """Подключение нового пользователя к чату"""
        if chat_id not in self.active_connections:
            self.active_connections[chat_id] = {}
        self.active_connections[chat_id][user_id] = websocket
        logger.info(f"User {user_id} connected to chat {chat_id}")

    async def disconnect(self, websocket: WebSocket, chat_id: int, user_id: int):
        """Отключение пользователя от чата"""
        if chat_id in self.active_connections:
            self.active_connections[chat_id].pop(user_id, None)
            if not self.active_connections[chat_id]:
                self.active_connections.pop(chat_id)
        logger.info(f"User {user_id} disconnected from chat {chat_id}")

    async def broadcast_message(self, chat_id: int, message: Any, current_user_id: int) -> None:
        """Отправка сообщения всем подключенным пользователям в чате"""
        if chat_id in self.active_connections:


            message_json = json.loads(
                json.dumps(message, cls=DateTimeEncoder)
            )

          

            # Отправляем сообщение всем подключенным пользователям
            for user_id, websocket in self.active_connections[chat_id].items():
                if user_id == current_user_id:  # Пропускаем текущего пользователя
                    continue
                    
                try:
                    # logger.info(f"TRYING to send message to user {user_id} in chat {chat_id}")
                    if websocket.application_state.CONNECTED:
                        if message_json["message_type"] == "new_message":
                            logger.info(f"УВЕДОМЛЕНИЯ О НОВОМ СООБЩЕНИИ: to user {user_id} in chat {chat_id} \n {message_json}")
                        if message_json["message_type"] == "read_status":
                            logger.info(f"СТАТУС ПРОЧТЕНИЯ: to user {user_id} in chat {chat_id} \n {message_json}")
                        if message_json["message_type"] == "user_status":
                            logger.info(f"СТАТУС ПОЛЬЗОВАТЕЛЯ: to user {user_id} in chat {chat_id} \n {message_json}")
    
                        await websocket.send_text(json.dumps(message_json, cls=DateTimeEncoder))
                        logger.info(f"Message sent successfully to user {user_id}")
                    else:
                        logger.warning(f"Websocket for user {user_id} is not in CONNECTED state")
                except Exception as e:
                    logger.error(f"Error sending message to user {user_id}: {str(e)}")

    async def send_user_status(self, chat_id: int, user_id: int, status: str):
        """Отправка статуса пользователя"""
        response = UserStatusResponse(
            response_type='user_status',
            user_id=user_id,
            status=status,
            timestamp=datetime.utcnow()
        )
        # await self.broadcast_message(chat_id, response, user_id)

    async def send_personal_message(self, chat_id: int, user_id: int, message: dict):
        """Отправка личного сообщения конкретному пользователю"""
        if chat_id in self.active_connections and user_id in self.active_connections[chat_id]:
            await self.active_connections[chat_id][user_id].send_json(message)

    def get_active_users(self, chat_id: int) -> list[int]:
        """Получение списка активных пользователей в чате"""
        return list(self.active_connections.get(chat_id, {}).keys())

    def is_user_connected(self, chat_id: int, user_id: int) -> bool:
        """Проверка, подключен ли пользователь к чату"""
        return chat_id in self.active_connections and user_id in self.active_connections[chat_id]

    async def handle_connection(self, websocket: WebSocket, chat_id: int, user_id: int):
        """Обработка нового подключения"""
        # Принимаем соединение
        await websocket.accept()
        # Техническая часть
        await self.connect(websocket, chat_id, user_id)
        # Бизнес-логика
        await self.send_user_status(chat_id, user_id, "connected")

    async def handle_disconnection(self, websocket: WebSocket, chat_id: int, user_id: int):
        """Обработка отключения"""
        # Бизнес-логика
        await self.send_user_status(chat_id, user_id, "disconnected")
        # Техническая часть
        await self.disconnect(websocket, chat_id, user_id) 