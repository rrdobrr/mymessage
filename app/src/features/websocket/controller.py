from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.logging import logger
from src.features.messages.services import MessageService
from src.features.users.schemas import UserInDB
from .session_manager import WebSocketSessionManager
from .message_handler import WebSocketMessageHandler, DateTimeEncoder
from .schemas import MessageWS, ResponseWS
import json

from starlette.websockets import WebSocketState





class WebSocketController:
    def __init__(
        self,
        session_manager: WebSocketSessionManager,
        message_handler: WebSocketMessageHandler,
        message_service: MessageService
    ):
        logger.info("Creating new WebSocketController instance")
        self.session_manager = session_manager
        self.message_handler = message_handler
        self.message_service = message_service
        logger.info("WebSocketController initialized with dependencies")

    def _extract_message_type(self, raw_data: str) -> WebSocketMessageType:
        """
        Извлекает и проверяет тип сообщения из raw данных.
        
        Args:
            raw_data: JSON строка с данными сообщения
            
        Returns:
            WebSocketMessageType: тип сообщения
            
        Raises:
            ValueError: если тип сообщения отсутствует или невалиден
        """
        try:
            data = json.loads(raw_data)
            message_type = data.get("message_type")
            if not message_type:
                raise ValueError("message_type is required")
            return message_type, data
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON format")

    async def process_chat_connection(
        self,
        websocket: WebSocket,
        chat_id: int,
        current_user: UserInDB,
    ):
        """
        Обработка WebSocket соединения для чата
        
        Args:
            websocket: WebSocket соединение
            chat_id: ID чата
            current_user: Текущий пользователь
        """
        try:
            await self.session_manager.handle_connection(websocket, chat_id, current_user.id)
            
            try:
                while True:
                    raw_data = await websocket.receive_text()
                    message = MessageWS.parse_raw(raw_data)  # Используем pydantic для парсинга
                    
                    response = await self.message_handler.process_message(
                        message=message,
                        chat_id=chat_id,
                        current_user=current_user
                    )
                    
                    await websocket.send_text(response.json())  # ResponseWS автоматически сериализуется
                    await self.session_manager.broadcast_message(chat_id, response)
                    
            except WebSocketDisconnect:
                logger.warning(f"WebSocket disconnected for user {current_user.id}")
            finally:
                await self.session_manager.handle_disconnection(websocket, chat_id, current_user.id)
                
        except Exception as e:
            logger.error(f"Fatal error in WebSocket handler: {str(e)}")
            if websocket.client_state != WebSocketState.DISCONNECTED:
                error_response = json.dumps({
                    "type": "error",
                    "error": str(e)
                })
                await websocket.send_text(error_response)
                await websocket.close(code=1011)

