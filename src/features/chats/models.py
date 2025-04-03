from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum, Table, ForeignKey
from sqlalchemy.orm import relationship
from src.core.db import Base
import enum

class ChatType(enum.Enum):
    """
    Перечисление типов чатов
    
    Attributes:
        PRIVATE: Личный чат между двумя пользователями
        GROUP: Групповой чат с множеством участников
    """
    PRIVATE = "private"
    GROUP = "group"

# Промежуточная таблица для связи many-to-many между пользователями и чатами
chat_members = Table(
    "chat_members",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("chat_id", Integer, ForeignKey("chats.id"), primary_key=True)
)

class Chat(Base):
    """
    Модель чата
    
    Attributes:
        id (int): Уникальный идентификатор чата
        name (str): Название чата (для групповых) или null для личных
        chat_type (ChatType): Тип чата (личный/групповой)
        created_by (int): ID создателя чата
        created_at (datetime): Дата и время создания
        members: Список участников чата (отношение many-to-many с User)
    """
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=True)  # null для личных чатов
    chat_type = Column(Enum(ChatType), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Отношения
    members = relationship("User", secondary=chat_members, backref="chats")
    creator = relationship("User", foreign_keys=[created_by]) 