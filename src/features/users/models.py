from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from src.core.db import Base


class User(Base):
    """
    Модель пользователя системы
    
    Attributes:
        id (int): Уникальный идентификатор пользователя
        username (str): Имя пользователя для входа в систему
        email (str): Email пользователя
        hashed_password (str): Хэшированный пароль
        created_at (datetime): Дата и время создания аккаунта
        updated_at (datetime): Дата и время последнего обновления
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow) 