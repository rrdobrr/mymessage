from datetime import datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logging import logger
from src.core.exceptions import (
    NotFoundException, 
    ForbiddenException,
    UserAlreadyExistsException,
    UserUpdateException
)
from src.features.users.repositories import UserRepository
from src.features.users.schemas import UserCreate, UserUpdate, UserInDB
from src.features.users.models import User


class UserService:
    def __init__(self, db: AsyncSession):
        self.repository = UserRepository(db)

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Получение пользователя по email
        
        Args:
            email: Email пользователя
            
        Returns:
            Optional[User]: Пользователь или None, если не найден
        """
        return await self.repository.get_by_email(email)

    async def get_user(self, user_id: int) -> User:
        """Получение пользователя по ID"""
        user = await self.repository.get_by_id(user_id)
        if not user:
            logger.warning(f"User not found: id={user_id}")
            raise NotFoundException(f"User {user_id} not found")
        return user

    async def get_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Получение списка пользователей"""
        return await self.repository.get_list(skip, limit)

    async def create_user(self, user_data: UserCreate) -> User:
        """Создание нового пользователя"""
        # Проверка существования email
        existing_email = await self.repository.get_by_email(user_data.email)
        if existing_email:
            logger.warning(f"Attempt to create user with existing email: {user_data.email}")
            raise UserAlreadyExistsException("Email already registered")
            
        # Проверка существования username
        existing_username = await self.repository.get_by_username(user_data.username)
        if existing_username:
            logger.warning(f"Attempt to create user with existing username: {user_data.username}")
            raise UserAlreadyExistsException("Username already taken")
            
        try:
            now = datetime.utcnow()
            # Создаем словарь с данными пользователя

            user_dict = {
                "email": user_data.email,
                "username": user_data.username,
                "hashed_password": user_data.password,  # здесь уже хэшированный пароль
                "is_active": True,
                "created_at": now,
                "updated_at": now
            }

            return await self.repository.create(user_dict)
        except Exception as e:
            logger.error(f"Failed to create user: {str(e)}")
            raise UserUpdateException("Failed to create user")
        



        

    async def update_user(self, user_id: int, user_update: UserUpdate, current_user: UserInDB) -> User:
        """Обновление данных пользователя"""
        user = await self.get_user(user_id)
        if user.id != current_user.id:
            logger.warning(f"User {current_user.id} attempted to update user {user_id}")
            raise ForbiddenException("Can only update own profile")
            
        # Проверка email при обновлении
        if user_update.email and user_update.email != user.email:
            existing_email = await self.repository.get_by_email(user_update.email)
            if existing_email:
                raise UserAlreadyExistsException("Email already registered")
                
        # Проверка username при обновлении
        if user_update.username and user_update.username != user.username:
            existing_username = await self.repository.get_by_username(user_update.username)
            if existing_username:
                raise UserAlreadyExistsException("Username already taken")
                
        try:
            return await self.repository.update(user, user_update)
        except Exception as e:
            logger.error(f"Failed to update user {user_id}: {str(e)}")
            raise UserUpdateException("Failed to update user")

    async def delete_user(self, user_id: int, current_user: UserInDB) -> User:
        """Удаление пользователя"""
        user = await self.get_user(user_id)
        if user.id != current_user.id:
            logger.warning(f"User {current_user.id} attempted to delete user {user_id}")
            raise ForbiddenException("Can only delete own account")
        return await self.repository.delete(user) 