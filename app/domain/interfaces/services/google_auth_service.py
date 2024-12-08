from abc import ABC, abstractmethod
from typing import Dict
from starlette.requests import Request

class IGoogleAuthenticationService(ABC):
    """Интерфейс для GoogleAuthenticationService."""

    @abstractmethod
    async def get_authorization_url(self, request: Request) -> str:
        """Получение URL для авторизации."""
        pass

    @abstractmethod
    async def authenticate(self, request: Request) -> Dict:
        """Аутентификация пользователя через Google."""
        pass

    @abstractmethod
    async def refresh_token(self, refresh_token: str) -> Dict:
        """Обновление токена доступа."""
        pass

    @abstractmethod
    async def revoke_token(self, token: str) -> None:
        """Отзыв токена доступа."""
        pass
