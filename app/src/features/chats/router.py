from fastapi import APIRouter, Depends, status
from typing import List, Union

from src.features.auth.dependencies import get_current_user
from src.features.users.schemas import UserInDB
from src.features.chats.dependencies import get_chat_service
from src.features.chats.schemas import (
    ChatCreate,
    ChatUpdate,
    ChatInDB,
    PersonalChatResponse,
    GroupChatResponse
)
from src.features.chats.models import ChatType
from src.core.logging import logger

router = APIRouter(tags=["chats"])


@router.post("/create", response_model=Union[PersonalChatResponse, GroupChatResponse])
async def create_new_chat(
    chat_data: ChatCreate,
    chat_service = Depends(get_chat_service),
    current_user: UserInDB = Depends(get_current_user)
):
    """Создание нового чата"""
    logger.info(f"Creating new chat: {chat_data}")
    logger.info(f"Creating new chat: {chat_data}")
    logger.info(f"Creating new chat: {chat_data}")
    logger.info(f"Creating new chat: {chat_data}")
    chat = await chat_service.create_chat(chat_data, current_user)
    logger.debug(f"Created chat: type={chat.chat_type}, id={chat.id}")
    
    if chat.chat_type == ChatType.PERSONAL:
        return PersonalChatResponse.from_orm(chat)
    
    # Для группового чата получаем участников и добавляем их к объекту
    members = await chat_service.repository.get_chat_members(chat.id)
    setattr(chat, 'members', members)
    return GroupChatResponse.from_orm(chat)


@router.get("/list", response_model=List[ChatInDB])
async def read_user_chats(
    chat_service = Depends(get_chat_service),
    current_user: UserInDB = Depends(get_current_user)
):
    """Получение списка чатов пользователя"""
    return await chat_service.get_user_chats(current_user)


@router.get("/{chat_id}", response_model=ChatInDB)
async def read_chat(
    chat_id: int,
    chat_service = Depends(get_chat_service),
    current_user: UserInDB = Depends(get_current_user)
):
    """Получение информации о чате"""
    return await chat_service.get_chat(chat_id, current_user)


@router.patch("/{chat_id}/update", response_model=ChatInDB)
async def update_chat_info(
    chat_id: int,
    chat_update: ChatUpdate,
    chat_service = Depends(get_chat_service),
    current_user: UserInDB = Depends(get_current_user)
):
    """Обновление информации о чате"""
    return await chat_service.update_chat(chat_id, chat_update, current_user)


@router.post("/{chat_id}/members/add", response_model=GroupChatResponse)
async def add_members_to_chat(
    chat_id: int,
    member_ids: List[int],
    chat_service = Depends(get_chat_service),
    current_user: UserInDB = Depends(get_current_user)
):
    """Добавление участников в чат"""
    return await chat_service.add_members(chat_id, member_ids, current_user)


@router.post("/{chat_id}/members/remove", response_model=ChatInDB)
async def remove_members_from_chat(
    chat_id: int,
    member_ids: List[int],
    chat_service = Depends(get_chat_service),
    current_user: UserInDB = Depends(get_current_user)
):
    """Удаление участников из чата"""
    return await chat_service.remove_members(chat_id, member_ids, current_user)
