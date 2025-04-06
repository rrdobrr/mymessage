from datetime import datetime
from pydantic import BaseModel, constr, Field

class MessageBase(BaseModel):
    text: constr(max_length=4000)

class MessageCreate(MessageBase):
    chat_id: int
    text: str = Field(..., min_length=1)

class MessageUpdate(BaseModel):
    text: str | None = None
    is_read: bool | None = None

class MessageInDB(MessageBase):
    id: int
    chat_id: int
    sender_id: int
    is_read: bool
    created_at: datetime
    updated_at: datetime
    read_by: list[int] = []

    class Config:
        from_attributes = True

class MessageResponse(BaseModel):
    id: int
    chat_id: int
    sender_id: int
    text: str
    created_at: datetime
    updated_at: datetime
    is_read: bool

    class Config:
        from_attributes = True

class WebSocketMessage(BaseModel):
    """Схема для входящих WebSocket сообщений"""
    text: constr(min_length=1, max_length=4000)
    message_type: str = Field(default="message")

class WebSocketResponse(BaseModel):
    """Схема для исходящих WebSocket сообщений"""
    type: str
    text: str
    timestamp: datetime
    user_id: int
    message_id: int | None = None

class WebSocketStatusMessage(BaseModel):
    """Схема для статусных сообщений WebSocket"""
    type: str
    user_id: int
    username: str | None = None
    timestamp: datetime
    message_id: int | None = None
    chat_id: int | None = None 