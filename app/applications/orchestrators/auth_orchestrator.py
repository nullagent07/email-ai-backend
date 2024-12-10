from app.domain.models.users import Users
from app.domain.models.oauth import OAuthCredentials
from fastapi import Request, Depends
from fastapi.exceptions import HTTPException
from starlette.responses import JSONResponse
from app.domain.interfaces.services.user_service import IUserService
from app.domain.interfaces.services.oauth_service import IOAuthService
from app.domain.interfaces.services.auth_service import IAuthenticationService
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

    async def google_handle_callback(self, request: Request) -> dict:
        """Обрабатывает callback от провайдера OAuth и возвращает токены."""
        try:
            auth_result = await self.auth_service.authenticate(request)
            user = await self.google_authenticate(auth_result)
            request.session.pop('oauth_state', None)
            
            # Возвращаем токены для установки в куки
            response_data = {
                "access_token": auth_result["access_token"]
            }
            
            if "refresh_token" in auth_result:
                response_data["refresh_token"] = auth_result["refresh_token"]
                
            return response_data
            
        except Exception as e:
            logger.error(f"Callback error: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка при аутентификации: {str(e)}"
            )

    async def handle_oauth_callback(self, request: Request) -> dict:
        """Обрабатывает OAuth callback в зависимости от провайдера."""
        try:
            provider = request.path_params.get('provider')
            
            # Словарь соответствия провайдеров и методов обработки
            provider_handlers = {
                'google': self.google_handle_callback,
                # Добавьте другие провайдеры здесь
                # 'github': self.github_handle_callback,
                # 'facebook': self.facebook_handle_callback,
            }
            
            if provider not in provider_handlers:
                raise HTTPException(
                    status_code=400,
                    detail=f"Неподдерживаемый провайдер: {provider}"
                )
            
            # Вызываем соответствующий метод обработки
            return await provider_handlers[provider](request)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Ошибка в handle_oauth_callback: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Ошибка при обработке OAuth callback: {str(e)}"
            )
