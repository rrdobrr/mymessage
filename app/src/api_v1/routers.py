from fastapi import APIRouter

from src.features.auth.router import router as auth_router
from src.features.users.router import router as users_router


api_router = APIRouter()

# Здесь будем подключать роутеры из features 
api_router.include_router(auth_router, prefix="/auth", tags=["auth"]) 
api_router.include_router(users_router, prefix="/users", tags=["users"])