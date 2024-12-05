from abc import ABC, abstractmethod
from typing import Dict
from app.domain.models.user import User

class IUserService(ABC):
    """Интерфейс для сервиса пользователей."""

    @abstractmethod
    async def create_user(self, user_data: Dict) -> User:
        """Создает нового пользователя."""
        pass

    @abstractmethod
    async def find_user_by_email(self, email: str) -> User:
        """Находит пользователя по email."""
        pass
