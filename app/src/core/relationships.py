from sqlalchemy.orm import relationship

from src.features.users.models import User
from src.features.chats.models import Chat
from src.features.messages.models import Message
from src.features.chats.members_model import chat_members
from src.features.messages.read_status_model import message_read_status


def setup_relationships():
    """Установка отношений между моделями"""
    
    # Отношения между User и Chat
    User.created_chats = relationship(
        "Chat",
        back_populates="creator",
        foreign_keys="Chat.creator_id",
        cascade="all, delete-orphan"
    )
    Chat.creator = relationship(
        "User",
        back_populates="created_chats",
        foreign_keys="Chat.creator_id"
    )

    # Отношения для участников чата (many-to-many)
    User.chats = relationship(
        "Chat",
        secondary=chat_members,
        back_populates="members",
        lazy="selectin"
    )
    Chat.members = relationship(
        "User",
        secondary=chat_members,
        back_populates="chats",
        lazy="selectin"
    )

    # Отношения для сообщений
    Message.sender = relationship(
        "User",
        back_populates="messages",
        lazy="selectin"
    )
    User.messages = relationship(
        "Message",
        back_populates="sender",
        cascade="all, delete-orphan"
    )

    Message.chat = relationship(
        "Chat",
        back_populates="messages",
        lazy="selectin"
    )
    Chat.messages = relationship(
        "Message",
        back_populates="chat",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    # Отношения для статусов прочтения сообщений
    Message.read_by = relationship(
        "User",
        secondary=message_read_status,
        back_populates="read_messages",
        cascade="all",
        lazy="selectin"
    )
    
    User.read_messages = relationship(
        "Message",
        secondary=message_read_status,
        back_populates="read_by",
        lazy="selectin"
    )



