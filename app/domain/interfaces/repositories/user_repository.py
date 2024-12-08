from abc import ABC, abstractmethod
from typing import Dict
from app.domain.models.users import Users

class IUserRepository(ABC):
    """Интерфейс для UserRepository."""

    @abstractmethod
    async def add_user(self, user_data: Dict) -> Users:
        """Добавляет нового пользователя в базу данных."""
        pass

    @abstractmethod
    async def get_user_by_email(self, email: str) -> Users:
        """Получает пользователя по email."""
        pass
