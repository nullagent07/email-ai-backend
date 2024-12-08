from abc import ABC, abstractmethod
from typing import Dict
from app.domain.models.users import Users

class IUserService(ABC):
    """Интерфейс для сервиса пользователей."""

    @abstractmethod
    async def create_user(self, user_data: Dict) -> Users:
        """Создает нового пользователя."""
        pass

    @abstractmethod
    async def find_user_by_email(self, email: str) -> Users:
        """Находит пользователя по email."""
        pass

    @abstractmethod
    async def find_user_by_id(self, user_id: str) -> "Users":
        """Находит пользователя по ID."""
        pass
