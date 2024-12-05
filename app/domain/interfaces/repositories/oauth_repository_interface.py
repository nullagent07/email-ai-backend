from abc import ABC, abstractmethod
from typing import Dict
from app.domain.models.oauth import OAuthCredentials

class IOAuthRepository(ABC):
    """Интерфейс для OAuthRepository."""

    @abstractmethod
    async def add_credentials(self, credentials_data: Dict) -> OAuthCredentials:
        """Добавляет новые OAuth учетные данные в базу данных."""
        pass

    @abstractmethod
    async def get_credentials_by_email(self, email: str) -> OAuthCredentials:
        """Получает OAuth учетные данные по email."""
        pass
