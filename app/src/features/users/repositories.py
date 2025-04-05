from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logging import logger
from src.features.users.models import User
from src.features.users.schemas import UserCreate, UserUpdate
from src.core.security import get_password_hash


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_email(self, email: str) -> Optional[User]:
        """Получение пользователя по email"""
        logger.debug(f"Getting user by email: {email}")
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Получение пользователя по ID"""
        logger.debug(f"Getting user by id: {user_id}")
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_list(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Получение списка пользователей"""
        logger.debug(f"Getting users list: skip={skip}, limit={limit}")
        result = await self.db.execute(select(User).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def create(self, user_data: dict) -> User:
        """Создание нового пользователя"""
        logger.info(f"Creating new user with email: {user_data['email']}")
        
        db_user = User(
            email=user_data["email"],
            username=user_data["username"],
            hashed_password=user_data["hashed_password"],
            is_active=user_data["is_active"],
            created_at=user_data["created_at"],
            updated_at=user_data["updated_at"]
        )
        
        try:
            self.db.add(db_user)
            await self.db.commit()
            await self.db.refresh(db_user)
            logger.info(f"Created new user: id={db_user.id}")
            return db_user
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            raise

    async def update(self, user: User, user_update: UserUpdate) -> User:
        """Обновление данных пользователя"""
        logger.debug(f"Updating user: id={user.id}")
        update_data = user_update.model_dump(exclude_unset=True)
        
        if "password" in update_data:
            update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
        
        try:
            for field, value in update_data.items():
                setattr(user, field, value)
            await self.db.commit()
            await self.db.refresh(user)
            logger.info(f"Updated user: id={user.id}")
            return user
        except Exception as e:
            logger.error(f"Error updating user: {str(e)}")
            raise

    async def delete(self, user: User) -> User:
        """Удаление пользователя"""
        logger.debug(f"Deleting user: id={user.id}")
        try:
            await self.db.delete(user)
            await self.db.commit()
            logger.info(f"Deleted user: id={user.id}")
            return user
        except Exception as e:
            logger.error(f"Error deleting user: {str(e)}")
            raise

    async def get_by_username(self, username: str) -> Optional[User]:
        """Получение пользователя по username"""
        logger.debug(f"Getting user by username: {username}")
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none() 