from typing import Dict, Type

from app.applications.services.auth.google_auth_service import GoogleAuthenticationService
from app.applications.services.auth.interfaces import AuthenticationService
from app.infrastructure.auth.google.adapter import GoogleAuthAdapter
from core.settings import get_app_settings


class AuthServiceFactory:
    """Фабрика для создания сервисов аутентификации."""

    _services: Dict[str, Type[AuthenticationService]] = {
        "google": GoogleAuthenticationService
    }

    def __init__(self):
        self._settings = get_app_settings()

    def create_service(self, provider: str) -> AuthenticationService:
        """Создание сервиса аутентификации для указанного провайдера."""
        if provider.lower() == "google":
            adapter = GoogleAuthAdapter()
            return GoogleAuthenticationService(adapter)
        
        raise ValueError(f"Неподдерживаемый провайдер аутентификации: {provider}")
