from dataclasses import dataclass
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.logging import logger
from src.features.messages.services import MessageService
from src.features.users.schemas import UserInDB
from .session_manager import WebSocketSessionManager
from .message_handler import WebSocketMessageHandler
from .schemas import MessageWS, ResponseWS
import json
from pydantic import TypeAdapter

from starlette.websockets import WebSocketState

from .utils import DateTimeEncoder

class WebSocketController:
    """Контроллер для обработки WebSocket соединений"""
    def __init__(
        self,
        session_manager: WebSocketSessionManager,
        message_handler: WebSocketMessageHandler,
        message_service: MessageService
    ):
        self.session_manager = session_manager
        self.message_handler = message_handler
        self.message_service = message_service

    async def process_chat_connection(
        self,
        websocket: WebSocket,
        chat_id: int,
        current_user: UserInDB
    ):
        """Обработка WebSocket соединения для чата"""
        try:
            # Подключаем пользователя
            await self.session_manager.handle_connection(websocket, chat_id, current_user.id)
            
            while True:
                try:
                    # Получаем сообщение
                    data = await websocket.receive_json()
                    message = TypeAdapter(MessageWS).validate_python(data)
                    
                    # Обрабатываем сообщение и получаем ответ
                    response = await self.message_handler.process_message(
                        message=message,
                        chat_id=chat_id,
                        current_user=current_user
                    )
                    logger.info(f"Sending direct response to sender {current_user.id}: {response}")
                    
                    # Отправляем ответ ТОЛЬКО отправителю
                    response_json = json.dumps(response.model_dump(), cls=DateTimeEncoder)
                    await websocket.send_text(response_json)
                    logger.info(f"Response sent successfully to user {current_user.id}")
                    
                except WebSocketDisconnect:
                    logger.info(f"Client disconnected normally: user_id={current_user.id}, chat_id={chat_id}")
                    break
                    
        except Exception as e:
            logger.error(f"WebSocket error: {str(e)}")
            raise
            
        finally:
            await self.session_manager.handle_disconnection(websocket, chat_id, current_user.id)

