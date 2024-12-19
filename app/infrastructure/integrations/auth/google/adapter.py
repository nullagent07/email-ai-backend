from typing import Dict

from starlette.requests import Request
from starlette.datastructures import URL
from authlib.integrations.starlette_client import StarletteOAuth2App
from google.oauth2 import id_token
from google.auth.transport import requests

from app.domain.interfaces.integrations.auth.google.adapter import IGoogleAuthAdapter
from app.infrastructure.integrations.auth.google.client import AuthlibGoogleClient
from core.settings import get_app_settings

settings = get_app_settings()

class GoogleAuthAdapter(IGoogleAuthAdapter):
    """Адаптер для аутентификации через Google OAuth."""

    def __init__(self, google_oauth_client: StarletteOAuth2App = None):
        """Инициализация адаптера."""
        self._client = AuthlibGoogleClient(google_oauth_client) if google_oauth_client else None

    async def get_authorization_url(self, request: Request) -> str:
        """Получение URL авторизации с состоянием."""
        if not self._client:
            raise RuntimeError("OAuth client not initialized")
        redirect_uri = str(request.url_for('callback', provider='google'))
        return await self._client.get_authorization_url(redirect_uri=redirect_uri, request=request)

    async def authenticate(self, request: Request) -> Dict:
        """Аутентификация пользователя."""
        if not self._client:
            raise RuntimeError("OAuth client not initialized")
        return await self._client.exchange_code(request)

    async def refresh_token(self, refresh_token: str) -> Dict:
        """Обновление токена доступа."""
        if not self._client:
            raise RuntimeError("OAuth client not initialized")
        return await self._client.refresh_token(refresh_token)

    async def revoke_token(self, token: str) -> None:
        """Отзыв токена доступа."""
        if not self._client:
            raise RuntimeError("OAuth client not initialized")
        await self._client.revoke_token(token)

    def create_authorization_url_state(self, request: Request) -> str:
        """Создание уникального состояния для URL авторизации через клиент."""
        if not self._client:
            raise RuntimeError("OAuth client not initialized")
        return self._client.create_authorization_url_state(request)

    async def verify_token(self, token: str, expected_audience: str = None) -> Dict:
        """
        Verify and decode Google token.
        
        Args:
            token: Token to verify
            expected_audience: Not used for PubSub tokens
            
        Returns:
            Dict: Decoded token information if valid
            
        Raises:
            ValueError: If token is invalid
        """
        try:
            # Remove Bearer prefix if present
            token = token.replace("Bearer ", "")
            
            # Verify the JWT token
            decoded_token = id_token.verify_oauth2_token(
                token,
                requests.Request(),
                audience=None,  # Allow any audience as it's dynamic (ngrok URL)
                clock_skew_in_seconds=10  # Add time tolerance
            )
            
            # Verify service account email
            if decoded_token.get('email') != settings.google_service_account:
                raise ValueError(f"Invalid service account email: {decoded_token.get('email')}")
                
            # Verify expiration
            if 'exp' not in decoded_token:
                raise ValueError("Token has no expiration time")
            
            return decoded_token
            
        except Exception as e:
            raise ValueError(f"Token verification failed: {str(e)}")