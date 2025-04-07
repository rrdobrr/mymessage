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

        self.active_connections: Dict[int, Dict[int, set[WebSocket]]] = defaultdict(lambda: defaultdict(set))

    async def connect(self, websocket: WebSocket, chat_id: int, user_id: int):
        """Подключение нового пользователя к чату"""
        self.active_connections[chat_id][user_id].add(websocket)
        logger.info(f"User {user_id} connected to chat {chat_id}. Active connections: {len(self.active_connections[chat_id][user_id])}")

    async def disconnect(self, websocket: WebSocket, chat_id: int, user_id: int):
        """Отключение пользователя от чата"""
        if chat_id in self.active_connections and user_id in self.active_connections[chat_id]:
            self.active_connections[chat_id][user_id].discard(websocket)
            if not self.active_connections[chat_id][user_id]:
                del self.active_connections[chat_id][user_id]
            if not self.active_connections[chat_id]:
                del self.active_connections[chat_id]
        logger.info(f"User {user_id} disconnected from chat {chat_id}")

    async def broadcast_message(self, chat_id: int, message: Any, current_user_id: int) -> None:
        """Отправка сообщения всем подключенным пользователям в чате"""
        if chat_id in self.active_connections:
            message_json = json.loads(json.dumps(message, cls=DateTimeEncoder))

            # Отправляем сообщение всем подключенным пользователям
            for user_id, websockets in self.active_connections[chat_id].items():
                if user_id == current_user_id:  # Пропускаем текущего пользователя
                    continue
                    
                for websocket in websockets:
                    try:
                        # Убираем проверку состояния - пусть WebSocket сам обрабатывает свои ошибки
                        match message_json["message_type"]:
                            case "new_message":
                                logger.info(f"УВЕДОМЛЕНИЯ О НОВОМ СООБЩЕНИИ: to user {user_id} in chat {chat_id} \n {message_json}")
                            case "read_status":
                                logger.info(f"СТАТУС ПРОЧТЕНИЯ: to user {user_id} in chat {chat_id} \n {message_json}")
                            case "user_status":
                                logger.info(f"СТАТУС ПОЛЬЗОВАТЕЛЯ: to user {user_id} in chat {chat_id} \n {message_json}")

                        await websocket.send_text(json.dumps(message_json, cls=DateTimeEncoder))
                        logger.info(f"Message sent successfully to user {user_id}")
                    except Exception as e:
                        logger.error(f"Error sending message to user {user_id}: {str(e)}")
                        # Не отключаем соединение здесь - пусть это делает основной обработчик

    async def send_user_status(self, chat_id: int, user_id: int, status: Literal["online", "offline"]):
        """Отправка статуса пользователя"""
        status_message = {
            "message_type": "user_status",
            "user_id": user_id,
            "status": status,
            "chat_id": chat_id,
            "timestamp": datetime.utcnow()
        }
        await self.broadcast_message(chat_id, status_message, user_id)

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
        await websocket.accept()
        await self.connect(websocket, chat_id, user_id)
        # Отправляем статус "online" всем участникам чата
        await self.send_user_status(chat_id, user_id, "online")

    async def handle_disconnection(self, websocket: WebSocket, chat_id: int, user_id: int):
        """Обработка отключения"""
        # Отправляем статус "offline" всем участникам чата
        if self.is_user_connected(chat_id, user_id):
            await self.send_user_status(chat_id, user_id, "offline")
        await self.disconnect(websocket, chat_id, user_id) 