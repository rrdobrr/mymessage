from fastapi import APIRouter, Depends, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import get_db
from src.features.auth.services import AuthService
from src.features.auth.schemas import Token
from src.features.users.schemas import UserCreate, UserInDB

router = APIRouter(tags=["auth"])


@router.post("/register", response_model=UserInDB)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
) -> UserInDB:
    """Регистрация нового пользователя"""
    auth_service = AuthService(db)
    return await auth_service.register(user_data)


@router.post("/token", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
) -> Token:
    """Получение токенов доступа"""
    auth_service = AuthService(db)
    return await auth_service.login(form_data)


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_db)
) -> Token:
    """Обновление токенов доступа"""
    auth_service = AuthService(db)
    return await auth_service.refresh_tokens(refresh_token) 