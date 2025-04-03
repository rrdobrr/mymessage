from datetime import datetime
from pydantic import BaseModel, constr, Field
from typing import List
from src.features.users.schemas import UserInDB
from enum import Enum

class ChatType(str, Enum):
    PERSONAL = "PERSONAL"
    GROUP = "GROUP"

class ChatBase(BaseModel):
    name: constr(max_length=100) | None = None
    chat_type: ChatType

class ChatCreate(ChatBase):
    name: str = Field(..., min_length=1)
    chat_type: ChatType
    member_ids: List[int] = Field(..., min_items=2)  # минимум 2 участника

class ChatUpdate(BaseModel):
    name: constr(max_length=100) | None = None
    member_ids: List[int] | None = None

class ChatInDB(ChatBase):
    id: int
    creator_id: int
    created_at: datetime
    updated_at: datetime
    members: List[UserInDB]

    class Config:
        from_attributes = True 