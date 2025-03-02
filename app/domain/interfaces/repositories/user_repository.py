from abc import ABC, abstractmethod
from typing import Dict, Optional
from uuid import UUID
from app.domain.models.users import Users

class IUserRepository(ABC):
    """Интерфейс для UserRepository."""

    @abstractmethod
    async def add_user(self, user_data: Dict) -> Users:
        """Добавляет нового пользователя в базу данных."""
        pass

    @abstractmethod
    async def get_user_by_email(self, email: str) -> Optional[Users]:
        """Получает пользователя по email."""
        pass

    @abstractmethod
    async def get_user_by_id(self, user_id: UUID) -> Optional[Users]:
        """Получает пользователя по ID."""
        pass
