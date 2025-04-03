

from src.core.db import Base
from sqlalchemy import Column, Integer, ForeignKey, Table, PrimaryKeyConstraint

# Промежуточная таблица для связи many-to-many между чатами и пользователями
chat_members = Table(
    "chat_members",
    Base.metadata,
    Column("chat_id", Integer, ForeignKey("chats.id", ondelete="CASCADE"), nullable=False),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    PrimaryKeyConstraint("chat_id", "user_id"),  # Составной первичный ключ
)