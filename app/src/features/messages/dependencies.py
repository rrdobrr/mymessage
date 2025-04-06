from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import get_db
from src.features.messages.services import MessageService
from src.features.messages.websocket_service import WebSocketService
from src.features.auth.dependencies import get_current_user

# Создаем синглтон для WebSocketService

_websocket_service = WebSocketService()


def get_websocket_service() -> WebSocketService:
    """
    Получение синглтона WebSocketService
    
    Returns:
        WebSocketService: Экземпляр сервиса для работы с WebSocket
    """
    return _websocket_service 

async def get_message_service(db: AsyncSession = Depends(get_db)) -> MessageService:
    return MessageService(db)
