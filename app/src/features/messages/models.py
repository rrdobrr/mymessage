from datetime import datetime
from sqlalchemy import Integer, String, DateTime, ForeignKey, func, ARRAY
from sqlalchemy.orm import Mapped, mapped_column
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
        updated_at (datetime): Время последнего обновления
        idempotency_key (str): Ключ идемпотентности
    """
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    chat_id: Mapped[int] = mapped_column(ForeignKey("chats.id", ondelete="CASCADE"), nullable=False)
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    text: Mapped[str]
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
    idempotency_key: Mapped[str] = mapped_column(String(64), unique=True, nullable=True)
   

