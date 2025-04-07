from fastapi import Depends, WebSocket
from sqlalchemy.ext.asyncio import AsyncSession
from jose import JWTError, jwt
from src.core.db import get_db
from src.core.security import get_token_from_websocket, SECRET_KEY, ALGORITHM
from src.features.auth.services import AuthService
from src.features.users.services import UserService
from src.features.users.schemas import UserInDB
from src.core.exceptions import InvalidTokenException, WebSocketAuthException, NotFoundException
from .controller import WebSocketController
from .session_manager import WebSocketSessionManager
from src.core.logging import logger
from src.features.messages.services import MessageService
from src.features.auth.dependencies import get_current_user
from .message_handler import WebSocketMessageHandler
from src.features.messages.dependencies import get_message_service

# Создаем глобальный экземпляр WebSocketSessionManager
websocket_manager = WebSocketSessionManager()

async def get_websocket_controller(
    message_service: MessageService = Depends(get_message_service)
) -> WebSocketController:
    """Получение экземпляра WebSocketController"""
    logger.info("Initializing WebSocketController")
    message_handler = WebSocketMessageHandler(message_service, websocket_manager)
    return WebSocketController(
        session_manager=websocket_manager,
        message_handler=message_handler,
        message_service=message_service
    )

async def get_current_user_ws(
    websocket: WebSocket,
    db = Depends(get_db)
) -> UserInDB:
    """Получение текущего пользователя из WebSocket соединения"""
    if "Authorization" in websocket.headers:
        token = websocket.headers["Authorization"].split(" ")[1]
        return await get_current_user(token, db)
    await websocket.close(code=4000)  # Unauthorized
    return None

async def get_message_service(db: AsyncSession = Depends(get_db)) -> MessageService:
    """Получение экземпляра MessageService"""
    logger.info("Initializing MessageService")
    return MessageService(db) 


