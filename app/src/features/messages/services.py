from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.logging import logger
from datetime import datetime

from src.core.exceptions import (
    NotFoundException,
    ForbiddenException,
    MessageException
)
from src.features.messages.repositories import MessageRepository
from src.features.messages.schemas import MessageCreate, MessageUpdate
from src.features.users.schemas import UserInDB
from src.features.chats.services import ChatService
from src.features.messages.models import Message


class MessageService:
    def __init__(self, db: AsyncSession):
        self.repository = MessageRepository(db)
        self.chat_service = ChatService(db)

    async def get_message(self, message_id: int, current_user: UserInDB) -> Message:
        """Получение сообщения по ID с проверкой прав доступа"""
        logger.info(f"Getting message {message_id} for user {current_user.id}")
        
        message = await self.repository.get_by_id(message_id)
        if not message:
            logger.warning(f"Message {message_id} not found")
            raise NotFoundException(f"Message {message_id} not found")
            
        chat = await self.chat_service.get_chat(message.chat_id)
        if current_user.id not in [m.id for m in chat.members]:
            logger.warning(f"User {current_user.id} attempted to access message {message_id} without chat membership")
            raise ForbiddenException("Not a chat member")
            
        return message

    async def create_message(self, message_data: MessageCreate, current_user: UserInDB) -> Message:
        """Создание нового сообщения"""
        logger.info(f"Creating message in chat {message_data.chat_id} by user {current_user.id}")
        
        chat = await self.chat_service.get_chat(message_data.chat_id)
        if not chat:
            logger.warning(f"Chat {message_data.chat_id} not found")
            raise NotFoundException(f"Chat {message_data.chat_id} not found")
            
        if current_user.id not in [m.id for m in chat.members]:
            logger.warning(f"User {current_user.id} attempted to create message in chat {chat.id} without membership")
            raise ForbiddenException("Not a chat member")
        
        try:
            now = datetime.utcnow()
            message_dict = message_data.model_dump()
            message_dict.update({
                "created_at": now,
                "updated_at": now,
                "sender_id": current_user.id
            })
            message = await self.repository.create(message_dict)
            logger.info(f"Message {message.id} created successfully")
            return message
        except Exception as e:
            logger.error(f"Error creating message: {str(e)}")
            raise MessageException("Failed to create message")

    async def update_message(self, message_id: int, message_update: MessageUpdate, current_user: UserInDB) -> Message:
        logger.info(f"Updating message {message_id} by user {current_user.id}")
        
        message = await self.get_message(message_id, current_user)
        if message.sender_id != current_user.id:
            logger.warning(f"User {current_user.id} attempted to edit message {message_id} owned by {message.sender_id}")
            raise ForbiddenException("Can only edit own messages")
            
        try:
            update_dict = message_update.model_dump(exclude_unset=True)
            update_dict["updated_at"] = datetime.utcnow()
            updated_message = await self.repository.update(message, update_dict)
            logger.info(f"Message {message_id} updated successfully")
            return updated_message
        except Exception as e:
            logger.error(f"Error updating message: {str(e)}")
            raise MessageException("Failed to update message")

    async def delete_message(self, message_id: int, current_user: UserInDB):
        logger.info(f"Deleting message {message_id} by user {current_user.id}")
        
        message = await self.get_message(message_id, current_user)
        if message.sender_id != current_user.id:
            logger.warning(f"User {current_user.id} attempted to delete message {message_id} owned by {message.sender_id}")
            raise ForbiddenException("Can only delete own messages")
            
        try:
            await self.repository.delete(message)
            logger.info(f"Message {message_id} deleted successfully")
            return message
        except Exception as e:
            logger.error(f"Error deleting message: {str(e)}")
            raise MessageException("Failed to delete message")

    async def get_chat_messages(self, chat_id: int, current_user: UserInDB, skip: int = 0, limit: int = 50):
        logger.info(f"Getting messages for chat {chat_id}, user {current_user.id}")
        
        chat = await self.chat_service.get_chat(chat_id)
        if not chat:
            logger.warning(f"Chat {chat_id} not found")
            raise NotFoundException(f"Chat {chat_id} not found")
            
        if current_user.id not in [m.id for m in chat.members]:
            logger.warning(f"User {current_user.id} attempted to access chat {chat_id} without membership")
            raise ForbiddenException("Not a chat member")
        
        try:
            messages = await self.repository.get_chat_messages(chat_id, skip, limit)
            logger.info(f"Retrieved {len(messages)} messages from chat {chat_id}")
            return messages
        except Exception as e:
            logger.error(f"Error getting chat messages: {str(e)}")
            raise MessageException("Failed to get chat messages")

    async def mark_as_read(self, message_id: int, current_user: UserInDB) -> Message:
        """Отметить сообщение как прочитанное"""
        message = await self.get_message(message_id, current_user)
        message_update = MessageUpdate(is_read=True)
        return await self.repository.update(message, message_update) 