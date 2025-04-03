from datetime import datetime
from pydantic import BaseModel, constr, Field

class MessageBase(BaseModel):
    text: constr(max_length=4000)

class MessageCreate(MessageBase):
    text: str = Field(..., min_length=1)
    chat_id: int
    sender_id: int

class MessageUpdate(MessageBase):
    is_read: bool | None = None

class MessageInDB(MessageBase):
    id: int
    chat_id: int
    sender_id: int
    is_read: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True 