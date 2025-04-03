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
    chat_id = Column(Integer, ForeignKey("chats.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    text = Column(String(4000), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_read = Column(Boolean, default=False)
    
    # Отношения
    chat = relationship("Chat", backref="messages")
    sender = relationship("User", backref="sent_messages") 