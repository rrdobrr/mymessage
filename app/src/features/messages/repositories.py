from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from typing import List, Optional
from src.core.logging import logger

from src.features.messages.models import Message
from src.features.messages.schemas import MessageCreate, MessageUpdate


class MessageRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, message_data: MessageCreate, sender_id: int) -> Message:
        logger.debug(f"Creating message in DB: chat_id={message_data.chat_id}, sender_id={sender_id}")
        try:
            db_message = Message(
                text=message_data.text,
                chat_id=message_data.chat_id,
                sender_id=sender_id
            )
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
        logger.debug(f"Updating message in DB: id={message.id}")
        try:
            for field, value in message_update.dict(exclude_unset=True).items():
                setattr(message, field, value)
            await self.db.commit()
            await self.db.refresh(message)
            logger.debug(f"Message updated in DB: id={message.id}")
            return message
        except Exception as e:
            logger.error(f"Error updating message in DB: {str(e)}")
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