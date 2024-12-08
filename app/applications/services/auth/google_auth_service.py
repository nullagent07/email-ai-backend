from typing import Dict
from starlette.requests import Request

from app.domain.interfaces.services.auth_service import IAuthenticationService
from app.domain.interfaces.adapters.auth_google import IGoogleAuthAdapter
from core.settings import get_app_settings


class GoogleAuthenticationService(IAuthenticationService):
    """Сервис аутентификации через Google."""

    def __init__(self, adapter: IGoogleAuthAdapter):
        self._adapter = adapter
        self._settings = get_app_settings()

    async def get_authorization_url(self, request: Request) -> str:
        """Получение URL для авторизации."""
        return await self._adapter.get_authorization_url(request)

    async def authenticate(self, request: Request) -> Dict:
        """Аутентификация пользователя через Google."""
        # TODO: Добавить сохранение пользователя в базу данных
        # TODO: Добавить создание сессии

        return await self._adapter.authenticate(request)

    async def refresh_token(self, refresh_token: str) -> Dict:
        """Обновление токена доступа."""
        return await self._adapter.refresh_token(refresh_token)

    async def revoke_token(self, token: str) -> None:
        """Отзыв токена доступа."""
        await self._adapter.revoke_token(token)
