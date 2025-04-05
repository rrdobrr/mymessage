from fastapi import APIRouter

from src.features.auth.router import router as auth_router
from src.features.users.router import router as users_router
from src.features.chats.router import router as chats_router
from src.features.messages.router import router as messages_router



api_router = APIRouter()

# Здесь будем подключать роутеры из features 
api_router.include_router(auth_router, prefix="/auth", tags=["auth"]) 
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(chats_router, prefix="/chats", tags=["chats"])
api_router.include_router(messages_router, prefix="/messages", tags=["messages"])
