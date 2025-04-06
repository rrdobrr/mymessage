from fastapi import APIRouter, Depends, status, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.logging import logger
from datetime import datetime
from pydantic import ValidationError

from src.core.db import get_db
from src.features.messages.dependencies import get_message_service, get_websocket_service
from src.features.messages.schemas import (
    MessageCreate,
    MessageUpdate,
    MessageInDB,
    WebSocketMessage,
    WebSocketResponse,
    WebSocketStatusMessage
)
from src.core.security import get_token_from_websocket
from src.features.auth.dependencies import get_current_user
from src.features.users.schemas import UserInDB
from src.features.messages.websocket_service import WebSocketService
from src.core.exceptions import InvalidTokenException, WebSocketException, WebSocketAuthException
from src.features.messages.services import MessageService
from src.core.logging import logger
from src.features.users.repositories import UserRepository

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

@router.websocket("/ws/chat/{chat_id}")
async def chat_websocket(
    websocket: WebSocket,
    chat_id: int,
    db: AsyncSession = Depends(get_db),
    ws_service: WebSocketService = Depends(get_websocket_service),
    message_service: MessageService = Depends(get_message_service)
):
    """WebSocket endpoint для чата"""
    connection_id = id(websocket)
    logger.info(f"WebSocket connection attempt - ID: {connection_id}")
    await ws_service.handle_connection(websocket, chat_id, db, message_service) 