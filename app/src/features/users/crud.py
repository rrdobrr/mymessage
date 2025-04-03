from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from src.core.security import get_password_hash
from .models import User
from .schemas import UserCreate

async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Получает пользователя по email"""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()

async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
    """Создает нового пользователя"""
    user = User(
        email=user_in.email,
        username=user_in.username,
        hashed_password=get_password_hash(user_in.password)
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user 