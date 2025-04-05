from datetime import datetime, timedelta
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logging import logger
from src.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
    SECRET_KEY,
    ALGORITHM,
    get_password_hash
)
from src.core.exceptions import (
    InvalidCredentialsException,
    InvalidTokenException,
    RefreshTokenException,
    UserAlreadyExistsException
)
from src.features.users.schemas import UserCreate, UserInDB
from src.features.users.services import UserService
from src.features.auth.schemas import Token


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_service = UserService(db)

    async def register(self, user_data: UserCreate) -> UserInDB:
        """
        Регистрация нового пользователя
        
        Args:
            user_data: Данные пользователя
            
        Returns:
            UserInDB: Данные созданного пользователя
            
        Raises:
            UserAlreadyExistsException: Если email уже занят
        """
        logger.info(f"Registering new user with email: {user_data.email}")
        
        # Проверяем существование пользователя
        existing_user = await self.user_service.get_user_by_email(user_data.email)
        if existing_user:
            logger.warning(f"Attempt to register with existing email: {user_data.email}")
            raise UserAlreadyExistsException("Email already registered")

        # Хэшируем пароль перед созданием пользователя
        hashed_password = get_password_hash(user_data.password)
        
        # Создаем новый объект UserCreate с хэшированным паролем
        new_user_data = UserCreate(
            email=user_data.email,
            username=user_data.username,
            password=hashed_password
        )

        return await self.user_service.create_user(new_user_data)

    async def login(self, form_data: OAuth2PasswordRequestForm) -> Token:
        """
        Аутентификация пользователя и создание токенов
        
        Args:
            form_data: Данные формы (username и password)
            
        Returns:
            Token: Access и refresh токены
            
        Raises:
            InvalidCredentialsException: Если неверные учетные данные
        """
        logger.info(f"Login attempt for user: {form_data.username}")
        
        # Получаем пользователя
        user = await self.user_service.get_user_by_email(form_data.username)
        if not user:
            logger.warning(f"Login attempt with non-existent email: {form_data.username}")
            raise InvalidCredentialsException()
        
        # Проверяем пароль
        if not verify_password(form_data.password, user.hashed_password):
            logger.warning(f"Invalid password for user: {form_data.username}")
            raise InvalidCredentialsException()
        
        # Создаем токены
        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)
        
        logger.info(f"Successful login for user: {user.id}")
        return Token(access_token=access_token, refresh_token=refresh_token)

    async def refresh_tokens(self, refresh_token: str) -> Token:
        """
        Обновление токенов доступа
        
        Args:
            refresh_token: Текущий refresh token
            
        Returns:
            Token: Новые access и refresh токены
            
        Raises:
            RefreshTokenException: Если refresh token невалидный
        """
        logger.info("Token refresh attempt")
        try:
            # Проверяем refresh token
            payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
            if payload.get("type") != "refresh":
                logger.warning("Invalid token type in refresh attempt")
                raise RefreshTokenException()
                
            user_id = payload.get("sub")
            if not user_id:
                logger.warning("No user ID in refresh token")
                raise RefreshTokenException()
                
            # Проверяем существование пользователя
            user = await self.user_service.get_user(int(user_id))
            
            # Создаем новые токены
            access_token = create_access_token(user.id)
            new_refresh_token = create_refresh_token(user.id)
            
            logger.info(f"Successfully refreshed tokens for user: {user.id}")
            return Token(
                access_token=access_token,
                refresh_token=new_refresh_token
            )
            
        except JWTError as e:
            logger.error(f"JWT decode error: {str(e)}")
            raise RefreshTokenException() 