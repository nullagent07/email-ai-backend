from pydantic import BaseModel

class UserResponse(BaseModel):
    """Схема ответа с информацией о пользователе."""
    name: str
    email: str
