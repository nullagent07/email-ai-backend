from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional


class UserResponse(BaseModel):
    """Схема ответа с данными пользователя."""
    name: str = Field(..., description="Имя пользователя")
    email: str = Field(..., description="Email пользователя")


class AuthenticationResponse(BaseModel):
    """Схема ответа при успешной аутентификации."""
    message: str = Field(..., description="Сообщение о результате операции")
    user: UserResponse = Field(..., description="Данные пользователя")


class TokenResponse(BaseModel):
    """Схема ответа с токеном."""
    access_token: str = Field(..., description="Токен доступа")
    refresh_token: Optional[str] = Field(None, description="Токен обновления")
    token_type: str = Field(default="bearer", description="Тип токена")
    expires_in: int = Field(..., description="Время жизни токена в секундах")
