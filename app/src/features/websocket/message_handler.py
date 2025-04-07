from datetime import datetime
from typing import Union
from pydantic import TypeAdapter
from src.core.logging import logger
from src.features.messages.services import MessageService
from src.features.users.schemas import UserInDB
from src.features.messages.schemas import MessageCreate
from .schemas import MessageWS, ResponseWS
from src.core.exceptions import NotFoundException, ForbiddenException
from .session_manager import WebSocketSessionManager
from .utils import DateTimeEncoder
import json

class WebSocketMessageHandler:
    def __init__(self, message_service: MessageService, session_manager: WebSocketSessionManager):
        self.message_service = message_service
        self.session_manager = session_manager
        
    async def process_message(
        self,
        message: MessageWS,
        chat_id: int,
        current_user: UserInDB
    ) -> ResponseWS:
        """Обработка входящего сообщения"""
        logger.info(f"Processing message: {message}")
        
        try:
            match message.message_type:
                case 'new_message':
                    return await self._handle_new_message(message, chat_id, current_user)
                case 'read_status':
                    logger.info(f"Processing read_status message: {message}")
                    return await self._handle_read_status(message, chat_id, current_user)
                case 'user_status':
                    logger.info(f"Processing user_status message: {message}")
                    return await self._handle_user_status(message, chat_id, current_user)
                case _:
                    raise ValueError(f"Unsupported message type: {message.message_type}")
                
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            raise

    async def _handle_new_message(
        self,
        message: MessageWS,
        chat_id: int,
        current_user: UserInDB
    ) -> ResponseWS:
        """Обработка нового сообщения"""
        try:
            message_create = MessageCreate(
                text=message.text,
                chat_id=chat_id,
                idempotency_key=message.idempotency_key
            )
            
            db_message = await self.message_service.create_message(
                message_data=message_create,
                current_user=current_user
            )
 

            notification_data = {
                "message_type": "new_message",
                "message_id": db_message.id,
                "chat_id": chat_id,
                "sender_id": current_user.id,
                "text": db_message.text,
                "timestamp": db_message.created_at
            }

            
            await self.session_manager.broadcast_message(
                chat_id=chat_id,
                message=notification_data,
                current_user_id=current_user.id
            )



            response_data = {
                "response_type": "new_message",
                "message_id": db_message.id,
                "chat_id": chat_id,
                "sender_id": current_user.id,
                "text": db_message.text,
                "timestamp": db_message.created_at
            }

            response_json = json.loads(
                json.dumps(response_data, cls=DateTimeEncoder)
            )

            logger.info(f"Return response: {response_json}")
            return TypeAdapter(ResponseWS).validate_python(response_json)
            
        except Exception as e:
            logger.error(f"Error handling new message: {str(e)}")
            raise

    async def _handle_read_status(
        self,
        message: MessageWS,
        chat_id: int,
        current_user: UserInDB
    ) -> ResponseWS:
        """Обработка статуса прочтения"""
        # Получаем сообщение из БД по id
        
        
        db_message = await self.message_service.get_message(message.message_id, current_user)
        if not db_message:
            logger.error(f"Message {message.message_id} not found")
            raise ValueError(f"Message {message.message_id} not found")
        # Обновляем статус прочтения используя id из БД
        await self.message_service.mark_as_read(message.message_id, current_user.id)
        logger.info(f"УСПЕХ")

        # Получаем список пользователей, прочитавших сообщение
        read_by = await self.message_service.get_message_readers(db_message.id)
        logger.info(f"Список пользователей, прочитавших сообщение: {read_by}")


        notification_data = {
            "message_type": "read_status",
            "message_id": db_message.id,
            "chat_id": chat_id,
            "sender_id": current_user.id,
            "text": db_message.text,
            "timestamp": db_message.created_at
        }

        logger.info(f"Отправляем уведомление о статусе прочтения: {notification_data}")
        await self.session_manager.broadcast_message(
            chat_id=chat_id,
            message=notification_data,
            current_user_id=current_user.id
        )



        response_data = {
            "response_type": "read_status",
            "message_id": message.message_id,
            "chat_id": chat_id,
            "reader_id": current_user.id,
            "read_by": read_by,
            "timestamp": datetime.utcnow()
        }
        return TypeAdapter(ResponseWS).validate_python(response_data)





    async def _handle_user_status(
        self,
        message: MessageWS,
        chat_id: int,
        current_user: UserInDB
    ) -> ResponseWS:
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
            chat = await self.message_service.chat_service.get_chat(chat_id, current_user)
            if not chat:
                raise NotFoundException(f"Chat {chat_id} not found")
                
            if current_user.id not in [m.id for m in chat.members]:
                raise ForbiddenException("Not a chat member")

            response_data = {
                "response_type": "user_status",
                "user_id": current_user.id,
                "status": message.status,
                "timestamp": datetime.utcnow(),
                "chat_id": chat_id
            }
            return TypeAdapter(ResponseWS).validate_python(response_data)
            
        except Exception as e:
            logger.error(f"Error handling user status: {str(e)}")
            raise 