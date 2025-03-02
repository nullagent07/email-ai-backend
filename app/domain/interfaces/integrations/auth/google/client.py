from abc import ABC, abstractmethod
from typing import Dict
from starlette.requests import Request

class IGoogleOAuthClient(ABC):
    """Интерфейс для клиента Google OAuth."""

    @abstractmethod
    async def get_authorization_url(self, redirect_uri: str, request: Request) -> str:
        """Получение URL для авторизации."""
        pass

    @abstractmethod
    async def exchange_code(self, request: Request) -> Dict:
        """Обмен кода авторизации на токены."""
        pass

    @abstractmethod
    async def refresh_token(self, refresh_token: str) -> Dict:
        """Обновление токена доступа."""
        pass

    @abstractmethod
    async def revoke_token(self, token: str) -> None:
        """Отзыв токена доступа."""
        pass