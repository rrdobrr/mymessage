from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from src.core.logging import logger
from src.core.exceptions import (
    NotFoundException,
    ForbiddenException,
    ValidationException,
    ChatCreateException,
    ChatMemberException,
    ChatUpdateException
)
from src.features.chats.repositories import ChatRepository
from src.features.users.repositories import UserRepository
from src.features.chats.schemas import ChatCreate, ChatUpdate, ChatType
from src.features.users.schemas import UserInDB
from src.features.chats.models import Chat

class ChatService:
    def __init__(self, db: AsyncSession):
        self.repository = ChatRepository(db)
        self.user_repository = UserRepository(db)

    async def create_chat(self, chat_data: ChatCreate, current_user: UserInDB) -> Chat:
        """Создание нового чата"""
        try:
            logger.info(f"Creating chat: {chat_data}")
            if chat_data.chat_type == ChatType.PERSONAL:
                if len(chat_data.member_ids) != 1:
                    raise ValidationException("Personal chat must have exactly one member")
                
                # Для личного чата сохраняем participant_id
                participant_id = chat_data.member_ids[0]
                participant = await self.user_repository.get_by_id(participant_id)
                if not participant:
                    raise NotFoundException(f"User {participant_id} not found")

                name = chat_data.name or f"Chat with {participant.username}"
                chat = Chat(
                    name=name,
                    chat_type=ChatType.PERSONAL,
                    creator_id=current_user.id,
                    participant_id=participant_id,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                return await self.repository.create_personal(chat)

            else:  # GroupChat
                if not chat_data.name:
                    name = f"Group chat {len(chat_data.member_ids)}"
                    raise ValidationException("Group chat must have a name")
                
                # Получаем участников для группового чата
                members = []
                for user_id in chat_data.member_ids:
                    logger.info(f"Getting user by id: {user_id}")
                    user = await self.user_repository.get_by_id(user_id)
                    if not user:
                        raise NotFoundException(f"User {user_id} not found")
                    members.append(user)

                # Добавляем создателя в список участников
                members.append(current_user)

                chat = Chat(
                    name=chat_data.name,
                    chat_type=ChatType.GROUP,
                    creator_id=current_user.id,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                chat = await self.repository.create_group(chat, members)
                
                # Получаем участников и добавляем их к объекту чата
                members = await self.repository.get_chat_members(chat.id)
                setattr(chat, 'members', members)
                
                return chat

        except Exception as e:
            logger.error(f"Error creating chat: {str(e)}")
            raise ChatCreateException("Failed to create chat")

    async def get_chat(self, chat_id: int, current_user: UserInDB) -> Chat:
        """Получение чата по ID"""
        try:
            chat = await self.repository.get_by_id(chat_id)
            if not chat:
                logger.warning(f"Chat {chat_id} not found")
                raise NotFoundException(f"Chat {chat_id} not found")

            # Получаем участников чата
            members = await self.repository.get_chat_members(chat.id)
            if current_user.id not in [m.id for m in members]:
                logger.warning(f"User {current_user.id} attempted to access chat {chat_id} without being a member")
                raise ForbiddenException("Not a chat member")

            # Устанавливаем участников для сериализации
            setattr(chat, 'members', members)
            return chat
        
        except (NotFoundException, ForbiddenException):
            raise
        except Exception as e:
            logger.error(f"Error getting chat {chat_id}: {str(e)}")
            raise ChatException(f"Failed to get chat {chat_id}")

    async def get_user_chats(self, current_user: UserInDB) -> List[Chat]:
        """Получение списка чатов пользователя"""
        return await self.repository.get_user_chats(current_user.id)

    async def update_chat(self, chat_id: int, chat_update: ChatUpdate, current_user: UserInDB) -> Chat:
        """Обновление информации о чате"""
        chat = await self.get_chat(chat_id, current_user)
        
        if chat.creator_id != current_user.id:
            logger.warning(f"User {current_user.id} attempted to update chat {chat_id} without being creator")
            raise ForbiddenException("Only chat creator can update chat info")
            
        try:
            update_dict = chat_update.model_dump(exclude_unset=True)
            update_dict["updated_at"] = datetime.utcnow()
            return await self.repository.update(chat, update_dict)
        except Exception as e:
            logger.error(f"Error updating chat: {str(e)}")
            raise ChatUpdateException("Failed to update chat")

    async def add_members(self, chat_id: int, member_ids: List[int], current_user: UserInDB) -> Chat:
        """Добавление участников в чат"""
        chat = await self.get_chat(chat_id, current_user)
        
        if chat.creator_id != current_user.id:
            logger.warning(f"User {current_user.id} attempted to add members to chat {chat_id} without being creator")
            raise ForbiddenException("Only chat creator can add members")

        if chat.chat_type == ChatType.PERSONAL:
            logger.warning(f"Attempted to add members to personal chat: {chat_id}")
            raise ValidationException("Cannot add members to personal chat")

        # Получаем текущих участников
        current_members = await self.repository.get_chat_members(chat.id)
        current_member_ids = {m.id for m in current_members}

        new_members = []
        for user_id in member_ids:
            if user_id in current_member_ids:
                raise ValidationException(f"User {user_id} is already a member")
            user = await self.user_repository.get_by_id(user_id)
            if not user:
                raise NotFoundException(f"User {user_id} not found")
            new_members.append(user)

        try:
            return await self.repository.add_members(chat, new_members)
        except Exception as e:
            logger.error(f"Error adding members to chat: {str(e)}")
            raise ChatMemberException("Failed to add members to chat")

    async def remove_members(self, chat_id: int, member_ids: List[int], current_user: UserInDB) -> Chat:
        """Удаление участников из чата"""
        chat = await self.get_chat(chat_id, current_user)
        
        if chat.creator_id != current_user.id:
            logger.warning(f"User {current_user.id} attempted to remove members from chat {chat_id} without being creator")
            raise ForbiddenException("Only chat creator can remove members")

        if chat.chat_type == ChatType.PERSONAL:
            logger.warning(f"Attempted to remove members from personal chat: {chat_id}")
            raise ValidationException("Cannot remove members from personal chat")

        if current_user.id in member_ids:
            logger.warning(f"User {current_user.id} attempted to remove themselves from chat {chat_id}")
            raise ValidationException("Cannot remove yourself using this endpoint")

        try:
            return await self.repository.remove_members(chat, member_ids)
        except Exception as e:
            logger.error(f"Error removing members from chat: {str(e)}")
            raise ChatMemberException("Failed to remove members from chat") 