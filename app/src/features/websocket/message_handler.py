from datetime import datetime
from typing import Union
from src.core.logging import logger
from src.features.messages.services import MessageService
from src.features.users.schemas import UserInDB
from src.features.messages.schemas import MessageCreate
from .schemas import (
    MessageWS,
    ResponseWS
)
from src.core.exceptions import NotFoundException, ForbiddenException

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class WebSocketMessageHandler:
    def __init__(self, message_service: MessageService):
        self.message_service = message_service
        
    async def process_message(
        self,
        message: MessageWS,
        chat_id: int,
        current_user: UserInDB
    ) -> ResponseWS:
        """Обработка входящего сообщения"""
        logger.info(f"Processing message: {message}")
        
        try:
            # Используем type discriminator для определения типа сообщения
            match message:
                case NewMessageWS():
                    return await self._handle_new_message(message, chat_id, current_user)
                case ReadStatusWS():
                    return await self._handle_read_status(message, chat_id, current_user)
                case UserStatusWS():
                    return await self._handle_user_status(message, chat_id, current_user)
                case _:
                    raise ValueError(f"Unsupported message type: {message.message_type}")
                
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}", exc_info=True)
            raise

    async def _handle_new_message(
        self,
        message: NewMessageWS,
        chat_id: int,
        current_user: UserInDB
    ) -> NewMessageResponse:
        """
        Обработка нового сообщения
        
        Args:
            message: Входящее сообщение
            chat_id: ID чата
            current_user: Текущий пользователь
            
        Returns:
            NewMessageResponse: Ответ с созданным сообщением
            
        Raises:
            MessageException: При ошибке создания сообщения
        """
        try:
            # Создаем сообщение через сервис
            message_create = MessageCreate(
                text=message.text,
                chat_id=chat_id,
                idempotency_key=message.idempotency_key
            )
            
            db_message = await self.message_service.create_message(
                message_data=message_create,
                current_user=current_user
            )
            
            # Формируем ответ
            return NewMessageResponse(
                type="new_message",
                message_id=db_message.id,
                chat_id=chat_id,
                sender_id=current_user.id,
                text=db_message.text,
                timestamp=db_message.created_at,  # Используем timestamp из БД
                is_read=db_message.is_read,
                read_by=db_message.read_by or []
            )
            
        except Exception as e:
            logger.error(f"Error handling new message: {str(e)}")
            raise

    async def _handle_read_status(
        self,
        message: ReadStatusWS,
        chat_id: int,
        current_user: UserInDB
    ) -> ReadStatusResponse:
        db_message = await self.message_service.mark_as_read(
            message_id=message.message_id,
            user_id=current_user
        )
        
        return ReadStatusResponse(
            type="read_status",
            message_id=message.message_id,
            chat_id=chat_id,
            reader_id=current_user.id,
            timestamp=datetime.utcnow()
        )

    async def _handle_user_status(
        self,
        message: UserStatusWS,
        chat_id: int,
        current_user: UserInDB
    ) -> UserStatusResponse:
        """
        Обработка статуса пользователя
        
        Args:
            message: Входящее сообщение о статусе
            chat_id: ID чата
            current_user: Текущий пользователь
            
        Returns:
            UserStatusResponse: Ответ со статусом пользователя
        """
        try:
            # Проверяем, что пользователь имеет доступ к чату
            chat = await self.message_service.chat_service.get_chat(chat_id, current_user)
            if not chat:
                raise NotFoundException(f"Chat {chat_id} not found")
                
            if current_user.id not in [m.id for m in chat.members]:
                raise ForbiddenException("Not a chat member")

            return UserStatusResponse(
                type="user_status",
                user_id=current_user.id,
                status=message.status,
                timestamp=datetime.utcnow(),
                chat_id=chat_id
            )
            
        except Exception as e:
            logger.error(f"Error handling user status: {str(e)}")
            raise 