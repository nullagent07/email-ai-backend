from abc import ABC, abstractmethod
from typing import Dict, Optional
from app.domain.models.oauth import OAuthCredentials
from uuid import UUID

class IOAuthService(ABC):
    """Интерфейс для OAuthService."""

    @abstractmethod
    async def create_credentials(self, credentials_data: Dict) -> OAuthCredentials:
        """Создает новые OAuth учетные данные."""
        pass

    @abstractmethod
    async def find_credentials_by_email(self, email: str) -> Optional[OAuthCredentials]:
        """Находит OAuth учетные данные по email."""
        pass

    @abstractmethod
    async def find_by_access_token(self, access_token: str) -> Optional[OAuthCredentials]:
        """Находит OAuth учетные данные по access token."""
        pass

    @abstractmethod
    async def update_credentials(self, email: str, provider: str, credentials_data: Dict) -> Optional[OAuthCredentials]:
        """Обновляет существующие OAuth учетные данные для конкретного провайдера."""
        pass
