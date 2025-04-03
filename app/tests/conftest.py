from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from src.features.users.models import User
from src.features.chats.models import Chat, ChatType
from src.features.messages.models import Message
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def create_test_data(session: AsyncSession):
    # Создаем пользователей
    users = [
        User(
            username=f"user{i}",
            email=f"user{i}@example.com",
            hashed_password=pwd_context.hash(f"password{i}")
        )
        for i in range(1, 4)
    ]
    session.add_all(users)
    await session.flush()

    # Создаем личный чат между первыми двумя пользователями
    personal_chat = Chat(
        name=None,
        chat_type=ChatType.PERSONAL,
        creator_id=users[0].id
    )
    personal_chat.members.extend([users[0], users[1]])
    session.add(personal_chat)

    # Создаем групповой чат со всеми пользователями
    group_chat = Chat(
        name="Test Group Chat",
        chat_type=ChatType.GROUP,
        creator_id=users[0].id
    )
    group_chat.members.extend(users)
    session.add(group_chat)
    await session.flush()

    # Добавляем сообщения
    messages = [
        Message(
            chat_id=personal_chat.id,
            sender_id=users[0].id,
            text="Hello, this is a personal message!",
            is_read=True
        ),
        Message(
            chat_id=personal_chat.id,
            sender_id=users[1].id,
            text="Hi! Nice to meet you!",
            is_read=False
        ),
        Message(
            chat_id=group_chat.id,
            sender_id=users[0].id,
            text="Welcome to the group chat!",
            is_read=False
        ),
        Message(
            chat_id=group_chat.id,
            sender_id=users[2].id,
            text="Thanks for adding me!",
            is_read=False
        )
    ]
    session.add_all(messages)
    await session.commit()

    return {
        "users": users,
        "personal_chat": personal_chat,
        "group_chat": group_chat,
        "messages": messages
    } 