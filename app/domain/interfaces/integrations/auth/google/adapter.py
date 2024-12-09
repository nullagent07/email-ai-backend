from abc import ABC, abstractmethod
from typing import Dict
from starlette.requests import Request

class IGoogleAuthAdapter(ABC):
    """Интерфейс адаптера для аутентификации через Google OAuth."""

    @abstractmethod
    async def get_authorization_url(self, request: Request) -> str:
        """Получение URL для авторизации."""
        pass

    @abstractmethod
    async def authenticate(self, request: Request) -> Dict:
        """Аутентификация пользователя."""
        pass

    @abstractmethod
    async def refresh_token(self, refresh_token: str) -> Dict:
        """Обновление токена доступа."""
        pass

    @abstractmethod
    async def revoke_token(self, token: str) -> None:
        """Отзыв токена доступа."""
        pass
