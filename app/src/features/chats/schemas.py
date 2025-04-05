from datetime import datetime
from pydantic import BaseModel, constr, Field, field_validator
from typing import List
from src.features.users.schemas import UserInDB
from src.features.chats.models import Chat, ChatType
from enum import Enum
from src.core.logging import logger



class ChatBase(BaseModel):
    name: str | None = None
    chat_type: ChatType

    class Config:
        from_attributes = True

class ChatCreate(BaseModel):
    """Schema for chat creation"""
    name: str | None = None
    chat_type: ChatType
    member_ids: list[int]

    @field_validator('member_ids')
    def validate_member_ids(cls, v, values):
        chat_type = values.data.get('chat_type')
        if chat_type == ChatType.PERSONAL and len(v) != 1:
            raise ValueError("Personal chat must have exactly one member")
        if chat_type == ChatType.GROUP and len(v) < 1:
            raise ValueError("Group chat must have at least one member")
        return v

    @field_validator('name')
    def validate_name(cls, v, values):
        chat_type = values.data.get('chat_type')
        if chat_type == ChatType.GROUP and not v:
            raise ValueError("Group chat must have a name")
        return v

class ChatUpdate(BaseModel):
    name: str | None = None

class ChatInDB(ChatBase):
    id: int
    creator_id: int
    created_at: datetime
    updated_at: datetime
    members: List[UserInDB]

    class Config:
        from_attributes = True

class PersonalChatResponse(BaseModel):
    id: int
    name: str
    chat_type: ChatType
    creator_id: int
    participant_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, chat: Chat) -> "PersonalChatResponse":
        return cls(
            id=chat.id,
            name=chat.name,
            chat_type=chat.chat_type,
            creator_id=chat.creator_id,
            participant_id=chat.participant_id,
            created_at=chat.created_at,
            updated_at=chat.updated_at
        )

class GroupChatResponse(BaseModel):
    id: int
    name: str
    chat_type: ChatType
    creator_id: int
    members: List[UserInDB]
    created_at: datetime
    updated_at: datetime
    participant_id: int | None = None

    model_config = {
        "from_attributes": True,
        "arbitrary_types_allowed": True
    }

    @classmethod
    def from_orm(cls, chat: Chat) -> "GroupChatResponse":
        """Создает объект ответа из модели"""
        logger.debug(f"Converting chat to GroupChatResponse. Chat id: {chat.id}")
        return cls(
            id=chat.id,
            name=chat.name,
            chat_type=chat.chat_type,
            creator_id=chat.creator_id,
            members=[UserInDB.from_orm(m) for m in chat.members],
            created_at=chat.created_at,
            updated_at=chat.updated_at
        ) 