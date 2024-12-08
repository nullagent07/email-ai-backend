from typing import Dict

from starlette.requests import Request
from authlib.integrations.starlette_client import StarletteOAuth2App

from app.domain.interfaces.adapters.auth_google import IGoogleAuthAdapter
from app.infrastructure.integrations.auth.google.client import AuthlibGoogleClient
from core.settings import get_app_settings
# from core.dependency_injection import google_oauth_client

settings = get_app_settings()

class GoogleAuthAdapter(IGoogleAuthAdapter):
    """Адаптер для аутентификации через Google OAuth."""

    def __init__(self, google_oauth_client: StarletteOAuth2App = None):
        """Инициализация адаптера."""
        self._client = AuthlibGoogleClient(google_oauth_client)

    async def get_authorization_url(self, request: Request) -> str:
        """Получение URL авторизации с состоянием."""
        redirect_uri = request.url_for('callback', provider='google')
        return await self._client.get_authorization_url(redirect_uri=redirect_uri, request=request)

    async def authenticate(self, request: Request) -> Dict:
        """Аутентификация пользователя."""
        return await self._client.exchange_code(request)

    async def refresh_token(self, refresh_token: str) -> Dict:
        """Обновление токена доступа."""
        return await self._client.refresh_token(refresh_token)

    async def revoke_token(self, token: str) -> None:
        """Отзыв токена доступа."""
        await self._client.revoke_token(token)

    def create_authorization_url_state(self, request: Request) -> str:
        """Создание уникального состояния для URL авторизации через клиент."""
        return self._client.create_authorization_url_state(request)