from enum import Enum
from pydantic import BaseModel, Field
from typing import Union, Literal, List
from src.features.messages.schemas import MessageCreate, MessageResponse
from datetime import datetime

class WebSocketMessageType(str, Enum):
    """Типы WebSocket сообщений"""
    NEW_MESSAGE = "new_message"  # Новое сообщение
    READ_STATUS = "read_status"  # Статус прочтения
    SYSTEM = "system"  # Системное сообщение
    USER_STATUS = "user_status"  # Статус пользователя

# Базовая схема для всех WebSocket сообщений
class BaseWebSocketMessage(BaseModel):
    """Базовая схема для всех WebSocket сообщений"""
    message_type: WebSocketMessageType = Field(..., discriminator="message_type")
    chat_id: int

# Схема входящего сообщения о новом сообщении
class NewMessageWS(BaseWebSocketMessage, MessageCreate):
    """Схема для нового сообщения"""
    message_type: Literal[WebSocketMessageType.NEW_MESSAGE]
    text: str


# Схема входяшего/исходящего сообщения о том что сообщение прочитано
class ReadStatusWS(BaseWebSocketMessage):
    """Схема для статуса прочтения"""
    message_type: Literal[WebSocketMessageType.READ_STATUS]
    message_id: int

# Схема исходящего сообщения о том что пользователь подключен или отключен
class UserStatusWS(BaseWebSocketMessage):
    """Схема для статуса пользователя"""
    message_type: Literal[WebSocketMessageType.USER_STATUS]
    user_id: int
    status: Literal["connected", "disconnected"]

# Схема для всех входящих сообщений
MessageWS = Union[NewMessageWS, ReadStatusWS, UserStatusWS]


# Базовая схема для всех ответов
class BaseWSResponse(BaseModel):
    """Базовая схема для всех ответов"""
    type: str = Field(..., discriminator="type")
    timestamp: datetime

# Схема ответа на новое сообщение
class NewMessageResponse(BaseWSResponse):
    """Схема ответа на новое сообщение"""
    type: Literal["new_message"]
    message_id: int
    chat_id: int
    sender_id: int
    text: str
    is_read: bool = False
    read_by: List[int] = []

# Схема ответа на статус прочтения. Схема исходящего сообщения о том что сообщение прочитано
class ReadStatusResponse(BaseWSResponse):
    """Схема ответа на статус прочтения"""
    type: Literal["read_status"]
    message_id: int
    chat_id: int
    reader_id: int

# Схема ответа на статус пользователя. Схема исходящего сообщения о том что пользователь подключен или отключен
class UserStatusResponse(BaseWSResponse):
    """Схема ответа на статус пользователя"""
    type: Literal["user_status"]
    user_id: int
    status: Literal["connected", "disconnected"]

# Объединенный тип для всех ответов
ResponseWS = Union[NewMessageResponse, ReadStatusResponse, UserStatusResponse]