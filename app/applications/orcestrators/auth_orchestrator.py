from app.domain.models.users import Users
from app.domain.models.oauth import OAuthCredentials
from fastapi import Request, Depends
from fastapi.exceptions import HTTPException
from starlette.responses import JSONResponse
from app.domain.interfaces.services.user_service_interface import IUserService
from app.domain.interfaces.services.oauth_service_interface import IOAuthService
from app.applications.services.auth.interfaces import IAuthenticationService
from datetime import datetime

import logging

logger = logging.getLogger(__name__)

class AuthOrchestrator:
    """Оркестратор для управления процессом аутентификации."""

    def __init__(self, user_service: IUserService, oauth_service: IOAuthService, auth_service: IAuthenticationService):
        self.user_service = user_service
        self.oauth_service = oauth_service
        self.auth_service = auth_service

    async def google_authenticate(self, auth_result: dict) -> Users:
        """Аутентифицирует пользователя через Google и обновляет или создает учетные записи."""
        userinfo = auth_result['userinfo']
        email = userinfo['email']

        # Проверяем, существует ли пользователь
        user = await self.user_service.find_user_by_email(email)
        if not user:
            # Создаем нового пользователя
            user = await self.user_service.create_user({
                'name': userinfo['name'],
                'email': email
            })

            # Обновляем или создаем учетные данные OAuth
            await self.oauth_service.create_credentials({
                'user_id': user.id,
                'provider': 'google',
                'access_token': auth_result['access_token'],
                'refresh_token': auth_result['refresh_token'],
                'expires_at': datetime.fromtimestamp(auth_result['expires_at']),
                'email': email,
                'provider_data': userinfo
            })
        else:
            # Обновляем учетные данные OAuth
            await self.oauth_service.update_credentials(
                email=email,
                provider='google',
                credentials_data={
                    'access_token': auth_result['access_token'],
                    'refresh_token': auth_result['refresh_token'],
                    'expires_at': datetime.fromtimestamp(auth_result['expires_at']),
                    'email': email,
                    'provider_data': userinfo
                }
            )

        return user

    async def google_handle_callback(self, request: Request) -> bool:
        """Обрабатывает callback от провайдера OAuth и управляет процессом аутентификации."""
        try:
            auth_result = await self.auth_service.authenticate(request)
            user = await self.google_authenticate(auth_result)
            request.session.pop('oauth_state', None)
            # user = JSONResponse({
            #     "message": "Аутентификация успешна",
            #     "user": {
            #         "id": user.id,
            #         "name": user.name,
            #         "email": user.email
            #     }
            # })
            return True
        except Exception as e:
            logger.error(f"Callback error: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка при аутентификации: {str(e)}"
            )
