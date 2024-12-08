from abc import ABC, abstractmethod
from typing import Dict
from app.domain.models.oauth import OAuthCredentials

class IOAuthService(ABC):
    """Интерфейс для OAuthService."""

    @abstractmethod
    async def create_credentials(self, credentials_data: Dict) -> OAuthCredentials:
        """Создает новые OAuth учетные данные."""
        pass

    @abstractmethod
    async def find_credentials_by_email(self, email: str) -> OAuthCredentials:
        """Находит OAuth учетные данные по email."""
        pass

    @abstractmethod
    async def update_credentials(self, email: str, provider: str, credentials_data: Dict) -> OAuthCredentials:
        """Обновляет существующие OAuth учетные данные для конкретного провайдера."""
        pass
