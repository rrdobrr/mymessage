from pydantic import BaseModel


class Token(BaseModel):
    """Схема токенов доступа"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Схема полезной нагрузки токена"""
    sub: str | None = None
    type: str | None = None 