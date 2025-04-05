from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.core.logging import logger
from src.features.chats.models import Chat
from src.features.users.models import User
from src.features.chats.schemas import ChatCreate, ChatUpdate
from src.features.chats.members_model import chat_members


class ChatRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, chat: Chat, creator_id: int, members: List[User]) -> Chat:
        """Создание нового чата"""
        logger.debug(f"Creating chat: {chat.name}, type={chat.chat_type}")
        try:
            chat.creator_id = creator_id
            
            # Сначала создаем чат
            self.db.add(chat)
            await self.db.commit()
            await self.db.refresh(chat)
            
            # Добавляем участников через промежуточную таблицу
            stmt = chat_members.insert().values([
                {"chat_id": chat.id, "user_id": member.id}
                for member in members
            ])
            await self.db.execute(stmt)
            await self.db.commit()
            
            # Получаем участников для сериализации
            chat_members_list = await self.get_chat_members(chat.id)
            setattr(chat, 'members', chat_members_list)
            
            logger.info(f"Created chat: id={chat.id}")
            return chat
        except Exception as e:
            logger.error(f"Error creating chat: {str(e)}")
            raise

    async def get_by_id(self, chat_id: int) -> Optional[Chat]:
        """Получение чата по ID"""
        logger.debug(f"Getting chat by id: {chat_id}")
        result = await self.db.execute(
            select(Chat)
            .join(chat_members)
            .where(Chat.id == chat_id)
        )
        return result.unique().scalar_one_or_none()

    async def get_user_chats(self, user_id: int) -> List[Chat]:
        """Получение всех чатов пользователя"""
        logger.debug(f"Getting chats for user: {user_id}")
        result = await self.db.execute(
            select(Chat)
            .join(chat_members)
            .where(chat_members.c.user_id == user_id)
        )
        chats = list(result.unique().scalars().all())
        
        # Для каждого чата получаем его участников
        for chat in chats:
            members = await self.get_chat_members(chat.id)
            setattr(chat, 'members', members)
        
        return chats

    async def update(self, chat: Chat, chat_update: ChatUpdate) -> Chat:
        """Обновление информации о чате"""
        logger.debug(f"Updating chat: id={chat.id}")
        try:
            update_data = chat_update.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                if field != "member_ids":  # Обрабатываем member_ids отдельно
                    setattr(chat, field, value)
            
            await self.db.commit()
            await self.db.refresh(chat)
            logger.info(f"Updated chat: id={chat.id}")
            return chat
        except Exception as e:
            logger.error(f"Error updating chat: {str(e)}")
            raise

    async def add_members(self, chat: Chat, new_members: List[User]) -> Chat:
        """Добавление участников в чат"""
        logger.debug(f"Adding members to chat: id={chat.id}")
        try:
            # Добавляем участников через промежуточную таблицу
            stmt = chat_members.insert().values([
                {"chat_id": chat.id, "user_id": member.id}
                for member in new_members
            ])
            await self.db.execute(stmt)
            await self.db.commit()
            
            # Получаем обновленный список участников
            members = await self.get_chat_members(chat.id)
            setattr(chat, 'members', members)
            
            logger.info(f"Added members to chat: id={chat.id}")
            return chat
        except Exception as e:
            logger.error(f"Error adding members to chat: {str(e)}")
            raise

    async def remove_members(self, chat: Chat, member_ids: List[int]) -> Chat:
        """Удаление участников из чата"""
        logger.debug(f"Removing members from chat: id={chat.id}")
        try:
            # Удаляем участников из промежуточной таблицы
            stmt = chat_members.delete().where(
                (chat_members.c.chat_id == chat.id) & 
                (chat_members.c.user_id.in_(member_ids))
            )
            await self.db.execute(stmt)
            await self.db.commit()
            
            # Получаем обновленный список участников
            remaining_members = await self.get_chat_members(chat.id)
            setattr(chat, 'members', remaining_members)
            
            logger.info(f"Removed members from chat: id={chat.id}")
            return chat
        except Exception as e:
            logger.error(f"Error removing members from chat: {str(e)}")
            raise

    async def create_personal(self, chat: Chat) -> Chat:
        """Создание личного чата"""
        try:
            self.db.add(chat)
            await self.db.commit()
            await self.db.refresh(chat)
            return chat
        except Exception as e:
            logger.error(f"Error creating personal chat: {str(e)}")
            raise

    async def get_chat_members(self, chat_id: int) -> List[User]:
        """Получение участников чата"""
        result = await self.db.execute(
            select(User)
            .join(chat_members)
            .where(chat_members.c.chat_id == chat_id)
        )
        return list(result.scalars().all())

    async def create_group(self, chat: Chat, members: List[User]) -> Chat:
        """Создание группового чата"""
        try:
            # Создаем чат
            self.db.add(chat)
            await self.db.commit()
            await self.db.refresh(chat)

            # Добавляем участников через промежуточную таблицу
            stmt = chat_members.insert().values([
                {"chat_id": chat.id, "user_id": member.id}
                for member in members
            ])
            await self.db.execute(stmt)
            await self.db.commit()
            
            # Получаем участников чата
            chat_members_list = await self.get_chat_members(chat.id)
            
            # Добавляем участников к объекту чата для сериализации
            setattr(chat, 'members', chat_members_list)
            
            logger.debug(f"Created group chat: id={chat.id} with {len(chat_members_list)} members")
            return chat
        except Exception as e:
            logger.error(f"Error creating group chat: {str(e)}")
            raise 