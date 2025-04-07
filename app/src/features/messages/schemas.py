from datetime import datetime
from pydantic import BaseModel, constr, Field
from typing import Optional, List



class MessageBase(BaseModel):
    text: constr(max_length=4000)

class MessageCreate(BaseModel):
    chat_id: int
    text: str

    idempotency_key: str | None = None

class MessageUpdate(BaseModel):
    message_id: int | None = None
    text: str | None = None
    is_read: bool | None = None
    read_by: list[int] | None = None
    idempotency_key: str | None = None

    class Config:
        from_attributes = True

class MessageInDB(MessageBase):
    id: int
    chat_id: int
    sender_id: int
    is_read: bool = False
    created_at: datetime
    updated_at: datetime
    read_by: list[int] = Field(default_factory=list)

    class Config:
        from_attributes = True

class MessageResponse(BaseModel):
    id: int
    chat_id: int
    sender_id: int
    text: str
    is_read: bool
    created_at: datetime
    updated_at: datetime
    read_by: list[int] = Field(default_factory=list)
    idempotency_key: str | None = None

    class Config:
        from_attributes = True

class MessageHistory(BaseModel):
    messages: List[MessageResponse]
    total: int
    has_more: bool

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
