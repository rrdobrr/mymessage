from pydantic import BaseModel, Field
from typing import Union, Literal, List, Annotated
from src.features.messages.schemas import MessageCreate
from datetime import datetime

# Базовая схема для всех WebSocket сообщений
class BaseWebSocketMessage(BaseModel):
    chat_id: int

    class Config:
        extra = "forbid"
        use_enum_values = True

# Схема входящего сообщения о новом сообщении
class NewMessageWS(BaseWebSocketMessage, MessageCreate):
    message_type: Literal['new_message']
    text: str

# Схема входящего сообщения о прочтении
class ReadStatusWS(BaseWebSocketMessage):
    message_type: Literal['read_status']
    message_id: int

# Схема сообщения о статусе пользователя
class UserStatusWS(BaseWebSocketMessage):
    message_type: Literal['user_status']
    user_id: int
    status: Literal["connected", "disconnected"]

# Базовая схема для всех ответов
class BaseWSResponse(BaseModel):
    response_type: str
    timestamp: datetime

# Схема ответа сервера на создание нового сообщения
class NewMessageResponse(BaseWSResponse):
    response_type: Literal['new_message']
    message_id: int
    chat_id: int
    sender_id: int
    text: str
    timestamp: datetime

# Схема ответа на статус прочтения
class ReadStatusResponse(BaseWSResponse):
    response_type: Literal['read_status']
    message_id: int
    chat_id: int
    reader_id: int
    read_by: List[int] = []

# Схема ответа на статус пользователя
class UserStatusResponse(BaseWSResponse):
    response_type: Literal['user_status']
    user_id: int
    status: Literal["connected", "disconnected"]
    timestamp: datetime

# Объединённый тип для входящих сообщений с дискриминатором
MessageWS = Annotated[
    Union[NewMessageWS, ReadStatusWS, UserStatusWS],
    Field(discriminator="message_type")
]

# Объединённый тип для ответов с дискриминатором
ResponseWS = Annotated[
    Union[NewMessageResponse, ReadStatusResponse, UserStatusResponse],
    Field(discriminator="response_type")
]