from datetime import datetime
from sqlalchemy import DateTime, Boolean, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class User(Base):
    """
    Модель пользователя системы
    
    Attributes:
        id (int): Уникальный идентификатор пользователя
        username (str): Имя пользователя для входа в систему
        email (str): Email пользователя
        hashed_password (str): Хэшированный пароль
        is_active (bool): Статус активности пользователя
        created_at (datetime): Дата и время создания аккаунта
        updated_at (datetime): Дата и время последнего обновления
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(200))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
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


