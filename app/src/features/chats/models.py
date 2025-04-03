from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table, Enum, PrimaryKeyConstraint
from sqlalchemy.orm import relationship
import enum
from src.core.db import Base

class ChatType(str, enum.Enum):
    PERSONAL = "personal"
    GROUP = "group"

# Промежуточная таблица для связи many-to-many между чатами и пользователями
chat_members = Table(
    "chat_members",
    Base.metadata,
    Column("chat_id", Integer, ForeignKey("chats.id", ondelete="CASCADE"), nullable=False),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    PrimaryKeyConstraint("chat_id", "user_id"),  # Составной первичный ключ
)

class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=True)  # Может быть NULL для личных чатов
    chat_type = Column(String, nullable=False)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Отношения
    members = relationship("User", secondary=chat_members, back_populates="chats")
    creator = relationship("User", back_populates="created_chats")
    messages = relationship("Message", back_populates="chat", cascade="all, delete-orphan") 