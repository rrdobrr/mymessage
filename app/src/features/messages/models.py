from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from src.core.db import Base


class Message(Base):
    """
    Модель сообщения в чате
    
    Attributes:
        id (int): Уникальный идентификатор сообщения
        chat_id (int): ID чата, к которому относится сообщение
        sender_id (int): ID отправителя
        text (str): Текст сообщения
        created_at (datetime): Время отправки сообщения
        is_read (bool): Признак прочтения сообщения
        read_by: Список пользователей, прочитавших сообщение
    """
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, ForeignKey("chats.id", ondelete="CASCADE"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    text = Column(String(4000), nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Отношения
    chat = relationship("Chat", back_populates="messages")
    sender = relationship("User", back_populates="messages") 