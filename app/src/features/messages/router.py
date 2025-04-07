from fastapi import APIRouter, Depends, status

from src.features.messages.dependencies import get_message_service
from src.features.messages.schemas import (
    MessageCreate,
    MessageUpdate,
    MessageInDB,

)

from src.features.auth.dependencies import get_current_user
from src.features.users.schemas import UserInDB



router = APIRouter(tags=["messages"])



@router.post("/create", response_model=MessageInDB, status_code=status.HTTP_201_CREATED)
async def create_new_message(
    message_data: MessageCreate,
    message_service = Depends(get_message_service),
    current_user: UserInDB = Depends(get_current_user)
):
    """Создание нового сообщения"""
    return await message_service.create_message(message_data, current_user)

@router.get("/{message_id}", response_model=MessageInDB)
async def read_message(
    message_id: int,
    message_service = Depends(get_message_service),
    current_user: UserInDB = Depends(get_current_user)
):
    """Получение конкретного сообщения"""
    return await message_service.get_message(message_id, current_user)

@router.patch("/{message_id}/update", response_model=MessageInDB)
async def update_message_text(
    message_id: int,
    message_update: MessageUpdate,
    message_service = Depends(get_message_service),
    current_user: UserInDB = Depends(get_current_user)
):
    """Обновление текста сообщения"""
    return await message_service.update_message(message_id, message_update, current_user)

@router.delete("/{message_id}/delete", response_model=MessageInDB)
async def delete_message_endpoint(
    message_id: int,
    message_service = Depends(get_message_service),
    current_user: UserInDB = Depends(get_current_user)
):
    """Удаление сообщения"""
    return await message_service.delete_message(message_id, current_user)

@router.post("/{message_id}/read", response_model=MessageInDB)
async def mark_message_as_read(
    message_id: int,
    message_service = Depends(get_message_service),
    current_user: UserInDB = Depends(get_current_user)
):
    """Отметить сообщение как прочитанное"""
    return await message_service.mark_as_read(message_id, current_user)

@router.get("/chat/{chat_id}", response_model=list[MessageInDB])
async def read_chat_messages(
    chat_id: int,
    skip: int = 0,
    limit: int = 50,
    message_service = Depends(get_message_service),
    current_user: UserInDB = Depends(get_current_user)
):
    """Получение сообщений чата"""
    return await message_service.get_chat_messages(chat_id, current_user, skip, limit)
