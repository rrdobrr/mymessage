from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
from typing import List
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from src.core.db import Base
from src.features.chats.members_model import chat_members
from src.features.users.models import User
from src.features.messages.models import Message


class ChatType(str, PyEnum):
    PERSONAL = "personal"
    GROUP = "group"


class Chat(Base):
    """Модель чата"""
    __tablename__ = "chats"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    chat_type: Mapped[ChatType] = mapped_column(String(50))
    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    participant_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )


