import pytest
from pydantic import ValidationError
import sys
from pathlib import Path
from datetime import datetime

# Добавляем родительскую директорию в путь для импортов
sys.path.append(str(Path(__file__).parent.parent))

from src.features.users.schemas import UserCreate, UserInDB
from src.features.chats.schemas import ChatCreate
from src.features.messages.schemas import MessageCreate

def test_user_validation():
    # Правильные данные для создания
    valid_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "strongpass123"
    }
    user = UserCreate(**valid_data)
    assert user.username == "testuser"
    
    # Неправильный email
    with pytest.raises(ValidationError):
        UserCreate(username="test", email="not_an_email", password="pass123")
    
    # Слишком короткий пароль
    with pytest.raises(ValidationError):
        UserCreate(username="test", email="test@example.com", password="123")

    # Проверка UserInDB
    user_db_data = {
        "username": "testuser",
        "email": "test@example.com",
        "hashed_password": "hashedpass123",
        "id": 1,
        "is_active": True,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    user_db = UserInDB(**user_db_data)
    assert user_db.id == 1
    assert user_db.is_active == True

def test_chat_validation():
    # Правильные данные
    valid_data = {
        "name": "Test Chat",
        "chat_type": "GROUP",
        "member_ids": [1, 2]
    }
    chat = ChatCreate(**valid_data)
    assert chat.name == "Test Chat"
    
    # Неправильный тип чата
    with pytest.raises(ValidationError):
        ChatCreate(name="Test", chat_type="INVALID_TYPE", member_ids=[1, 2])

    # Слишком мало участников
    with pytest.raises(ValidationError):
        ChatCreate(name="Test", chat_type="GROUP", member_ids=[1])

def test_message_validation():
    # Правильные данные
    valid_data = {
        "text": "Hello!",
        "chat_id": 1,
        "sender_id": 1
    }
    message = MessageCreate(**valid_data)
    assert message.text == "Hello!"
    
    # Пустое сообщение
    with pytest.raises(ValidationError):
        MessageCreate(text="", chat_id=1, sender_id=1)

if __name__ == "__main__":
    pytest.main([__file__])