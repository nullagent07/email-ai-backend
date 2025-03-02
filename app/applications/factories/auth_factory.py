from typing import Dict, Type

from app.applications.services.auth.google_auth_service import GoogleAuthenticationService
from app.domain.interfaces.services.auth_service import IAuthenticationService
from app.infrastructure.integrations.auth.google.adapter import GoogleAuthAdapter
from core.settings import get_app_settings

from authlib.integrations.starlette_client import StarletteOAuth2App


class AuthServiceFactory:
    """Фабрика для создания сервисов аутентификации."""

    _services: Dict[str, Type[IAuthenticationService]] = {
        "google": GoogleAuthenticationService
    }

    def __init__(self, google_oauth_client: StarletteOAuth2App):
        self._settings = get_app_settings()
        self._google_oauth_client = google_oauth_client

    def create_service(self, provider: str) -> IAuthenticationService:
        """Создание сервиса аутентификации для указанного провайдера."""
        if provider.lower() == "google":
            adapter = GoogleAuthAdapter(self._google_oauth_client)
            return GoogleAuthenticationService(adapter)
        
        raise ValueError(f"Неподдерживаемый провайдер аутентификации: {provider}")
