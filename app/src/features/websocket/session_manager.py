from fastapi import WebSocket
from typing import Dict, Union
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

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class WebSocketSessionManager:
    def __init__(self):
        # Структура: {chat_id: {user_id: websocket}}
        self.active_connections: Dict[int, Dict[int, WebSocket]] = {}

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

    async def broadcast_message(self, chat_id: int, message: Union[NewMessageResponse, ReadStatusResponse, UserStatusResponse]):
        """Рассылка сообщения всем участникам чата"""
        if chat_id in self.active_connections:
            message_json = message.json()
            for websocket in self.active_connections[chat_id].values():
                await websocket.send_text(message_json)

    async def send_user_status(self, chat_id: int, user_id: int, status: str):
        """Отправка статуса пользователя"""
        response = UserStatusResponse(
            type="user_status",
            user_id=user_id,
            status=status,
            timestamp=datetime.utcnow()
        )
        await self.broadcast_message(chat_id, response)

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