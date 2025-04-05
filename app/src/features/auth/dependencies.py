from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logging import logger
from src.core.db import get_db
from src.core.security import SECRET_KEY, ALGORITHM
from src.core.exceptions import InvalidTokenException
from src.features.users.services import UserService
from src.features.users.schemas import UserInDB

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> UserInDB:
    """
    Получение текущего пользователя из токена
    
    Args:
        token: JWT токен
        db: Сессия базы данных
        
    Returns:
        UserInDB: Текущий пользователь
        
    Raises:
        InvalidTokenException: Если токен невалидный
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            logger.warning("No user ID in token")
            raise InvalidTokenException()
            
        user_service = UserService(db)
        user = await user_service.get_user(int(user_id))
        if user is None:
            logger.warning(f"User from token not found: {user_id}")
            raise InvalidTokenException()
            
        return user
        
    except JWTError as e:
        logger.error(f"JWT decode error: {str(e)}")
        raise InvalidTokenException() 