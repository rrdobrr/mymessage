from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from typing import Any, Dict, Optional
from loguru import logger


class AppException(HTTPException):
    """Базовое исключение приложения"""
    def __init__(
        self,
        status_code: int,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.details = details
        super().__init__(status_code=status_code, detail=message)


class UserException(Exception):
    """Базовый класс для пользовательских исключений"""
    def __init__(self, message: str = None, details: dict = None):
        self.message = message
        self.details = details
        self.status_code = 500  # По умолчанию
        super().__init__(self.message)


class NotFoundException(UserException):
    """Исключение когда ресурс не найден"""
    def __init__(self, message: str = None, details: dict = None):
        super().__init__(message=message, details=details)
        self.status_code = 404  # Not Found


class ForbiddenException(UserException):
    """Исключение при отсутствии прав доступа"""
    def __init__(self, message: str = None, details: dict = None):
        super().__init__(message=message, details=details)
        self.status_code = 403  # Forbidden


class ValidationException(UserException):
    """Исключение при ошибках валидации"""
    def __init__(self, message: str = None, details: dict = None):
        super().__init__(message=message, details=details)
        self.status_code = 400  # Bad Request


class AuthenticationException(AppException):
    """Исключение для ошибок аутентификации"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=401, message=message, details=details)


class MessageException(UserException):
    """Исключение при ошибках с сообщениями"""
    def __init__(self, message: str = None, details: dict = None):
        super().__init__(message=message, details=details)
        self.status_code = 400


class UserAlreadyExistsException(UserException):
    """Исключение при попытке создать пользователя с существующим email/username"""
    def __init__(self, message: str = None, details: dict = None):
        super().__init__(message=message, details=details)
        self.status_code = 409  # Conflict


class UserUpdateException(UserException):
    """Исключение при ошибке обновления пользователя"""
    def __init__(self, message: str = None, details: dict = None):
        super().__init__(message=message, details=details)
        self.status_code = 400


class ChatException(AppException):
    """Базовое исключение для операций с чатами"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=400, message=message, details=details)


class ChatCreateException(UserException):
    """Исключение при ошибке создания чата"""
    def __init__(self, message: str = None, details: dict = None):
        super().__init__(message=message, details=details)
        self.status_code = 400


class ChatMemberException(UserException):
    """Исключение при ошибках с участниками чата"""
    def __init__(self, message: str = None, details: dict = None):
        super().__init__(message=message, details=details)
        self.status_code = 400


class ChatUpdateException(UserException):
    """Исключение при ошибке обновления чата"""
    def __init__(self, message: str = None, details: dict = None):
        super().__init__(message=message, details=details)
        self.status_code = 400


class AuthException(AppException):
    """Базовое исключение для аутентификации/авторизации"""
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=401, message=message, details=details)


class InvalidCredentialsException(UserException):
    """Исключение при неверных учетных данных"""
    def __init__(self, message: str = None, details: dict = None):
        super().__init__(message=message, details=details)
        self.status_code = 401  # Unauthorized


class InvalidTokenException(UserException):
    """Исключение при проблемах с токеном"""
    def __init__(self, message: str = None, details: dict = None):
        super().__init__(message=message, details=details)
        self.status_code = 401  # Unauthorized


class TokenExpiredException(AuthException):
    """Исключение при истекшем токене"""
    def __init__(self, message: str = "Token has expired", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, details=details)


class RefreshTokenException(UserException):
    """Исключение при проблемах с refresh token"""
    def __init__(self, message: str = None, details: dict = None):
        super().__init__(message=message, details=details)
        self.status_code = 401  # Unauthorized


async def app_exception_handler(request: Request, exc: AppException):
    """Обработчик кастомных исключений"""
    logger.error(
        f"Exception occurred: {exc.message}",
        extra={
            "status_code": exc.status_code,
            "details": exc.details,
            "path": request.url.path
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "message": exc.message,
            "details": exc.details,
            "status_code": exc.status_code,
        },
    )


def setup_exception_handlers(app):
    """Регистрация обработчика исключений"""
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(NotFoundException, app_exception_handler)
    app.add_exception_handler(ForbiddenException, app_exception_handler)
    app.add_exception_handler(ValidationException, app_exception_handler)
    app.add_exception_handler(AuthenticationException, app_exception_handler)
    app.add_exception_handler(MessageException, app_exception_handler)
    app.add_exception_handler(UserException, app_exception_handler)
    app.add_exception_handler(UserAlreadyExistsException, app_exception_handler)
    app.add_exception_handler(UserUpdateException, app_exception_handler)
    app.add_exception_handler(ChatException, app_exception_handler)
    app.add_exception_handler(ChatCreateException, app_exception_handler)
    app.add_exception_handler(ChatMemberException, app_exception_handler)
    app.add_exception_handler(ChatUpdateException, app_exception_handler)
    app.add_exception_handler(AuthException, app_exception_handler)
    app.add_exception_handler(InvalidCredentialsException, app_exception_handler)
    app.add_exception_handler(InvalidTokenException, app_exception_handler)
    app.add_exception_handler(TokenExpiredException, app_exception_handler)
    app.add_exception_handler(RefreshTokenException, app_exception_handler) 