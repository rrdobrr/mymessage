from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import get_db
from src.features.chats.services import ChatService


async def get_chat_service(db: AsyncSession = Depends(get_db)) -> ChatService:
    return ChatService(db) 