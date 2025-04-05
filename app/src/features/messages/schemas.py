from datetime import datetime
from pydantic import BaseModel, constr, Field

class MessageBase(BaseModel):
    text: constr(max_length=4000)

class MessageCreate(MessageBase):
    chat_id: int
    sender_id: int
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