from datetime import datetime
from sqlalchemy import select, insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from typing import List, Optional
from src.core.logging import logger

from src.features.messages.models import Message
from src.features.messages.schemas import MessageCreate, MessageUpdate
from src.features.messages.read_status_model import message_read_status


class MessageRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, message_data: MessageCreate, sender_id: int) -> Message:
        logger.debug(f"Creating message in DB: chat_id={message_data.chat_id}, sender_id={sender_id}")
        try:
            # Преобразуем message_data в словарь и добавляем sender_id
            message_dict = message_data.model_dump()
            message_dict["sender_id"] = sender_id
            
            # Создаем сообщение, используя все поля из message_dict
            db_message = Message(**message_dict)
            
            self.db.add(db_message)
            await self.db.commit()
            await self.db.refresh(db_message)
            logger.debug(f"Message created in DB: id={db_message.id}")
            return db_message
        except Exception as e:
            logger.error(f"Error creating message in DB: {str(e)}")
            raise

    async def get_by_id(self, message_id: int) -> Optional[Message]:
        logger.debug(f"Getting message from DB: id={message_id}")
        result = await self.db.execute(
            select(Message)
            .options(
                joinedload(Message.sender),
                joinedload(Message.chat)
            )
            .where(Message.id == message_id)
        )
        return result.scalar_one_or_none()

    async def get_chat_messages(
        self,
        chat_id: int,
        skip: int = 0,
        limit: int = 50
    ) -> List[Message]:
        logger.debug(f"Getting chat messages from DB: chat_id={chat_id}, skip={skip}, limit={limit}")
        result = await self.db.execute(
            select(Message)
            .options(
                joinedload(Message.sender),
                joinedload(Message.chat)
            )
            .where(Message.chat_id == chat_id)
            .offset(skip)
            .limit(limit)
            .order_by(Message.created_at.desc())
        )
        return list(result.scalars().unique())

    async def update(self, message: Message, message_update: MessageUpdate) -> Message:
        """Обновление сообщения"""
        try:
            update_dict = message_update.model_dump(exclude_unset=True)
            
            # Обновляем все поля из update_dict
            for field, value in update_dict.items():
                setattr(message, field, value)
            
            message.updated_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(message)
            
            return message
        except Exception as e:
            logger.error(f"Error updating message: {str(e)}")
            raise

    async def delete(self, message: Message) -> None:
        logger.debug(f"Deleting message from DB: id={message.id}")
        try:
            await self.db.delete(message)
            await self.db.commit()
            logger.debug(f"Message deleted from DB: id={message.id}")
        except Exception as e:
            logger.error(f"Error deleting message from DB: {str(e)}")
            raise

    async def get_by_idempotency_key(self, idempotency_key: str) -> Optional[Message]:
        """Получение сообщения по idempotency ключу"""
        query = select(Message).where(Message.idempotency_key == idempotency_key)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_read_status(self, message_id: int, user_id: int) -> None:
        """
        Создает запись о прочтении сообщения
        
        Args:
            message_id: ID сообщения
            user_id: ID пользователя
        """
        logger.debug(f"Creating read status: message_id={message_id}, user_id={user_id}")

        try:
            stmt = insert(message_read_status).values(
                message_id=message_id,
                user_id=user_id,
                read_at=datetime.utcnow()
            )
            await self.db.execute(stmt)
            await self.db.commit()
            logger.debug("Read status created successfully")
        except Exception as e:
            logger.error(f"Error creating read status: {str(e)}")
            raise

    async def get_message_readers(self, message_id: int) -> List[int]:
        """
        Получает список ID пользователей, прочитавших сообщение
        
        Args:
            message_id: ID сообщения
            
        Returns:
            List[int]: Список ID пользователей
        """
        logger.debug(f"Getting readers for message: {message_id}")
        try:
            query = select(message_read_status.c.user_id).where(
                message_read_status.c.message_id == message_id
            )
            result = await self.db.execute(query)
            return [row[0] for row in result.fetchall()]
        except Exception as e:
            logger.error(f"Error getting message readers: {str(e)}")
            raise 