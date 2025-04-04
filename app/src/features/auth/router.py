from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta
from typing import Optional
from jose import JWTError, jwt

from src.core.db import get_db
from src.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
    Token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    SECRET_KEY,
    ALGORITHM
)
from src.features.users.schemas import UserCreate, UserInDB
from src.features.users.crud import create_user, get_user_by_email, get_user_by_id

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.post("/register", response_model=UserInDB)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db)
) -> UserInDB:
    """
    Регистрация нового пользователя
    
    Args:
        user_in: Данные пользователя
        db: Сессия базы данных
        
    Returns:
        UserInDB: Данные созданного пользователя
    
    Raises:
        HTTPException: Если email уже занят
    """
    # Проверяем, не занят ли email
    existing_user = await get_user_by_email(db, user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    
    # Создаем пользователя
    user = await create_user(db, user_in)
    return user

@router.post("/token", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
) -> Token:
    """
    Получение JWT токенов
    
    Args:
        form_data: Данные формы (username и password)
        db: Сессия базы данных
        
    Returns:
        Token: Access и refresh токены
        
    Raises:
        HTTPException: Если неверные учетные данные
    """
    # Получаем пользователя по email
    user = await get_user_by_email(db, form_data.username)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password"
        )
    
    # Проверяем пароль
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password"
        )
    
    # Создаем токены
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token
    )

@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise credentials_exception
            
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
            
        user = await get_user_by_id(db, int(user_id))
        if user is None:
            raise credentials_exception
            
        return Token(
            access_token=create_access_token(user.id),
            refresh_token=create_refresh_token(user.id)
        )
    except JWTError:
        raise credentials_exception 