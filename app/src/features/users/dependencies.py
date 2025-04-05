from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import get_db
from src.features.users.services import UserService


async def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(db) 