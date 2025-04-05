from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import get_db
from src.features.messages.services import MessageService
from src.features.auth.dependencies import get_current_user


async def get_message_service(db: AsyncSession = Depends(get_db)) -> MessageService:
    return MessageService(db) 