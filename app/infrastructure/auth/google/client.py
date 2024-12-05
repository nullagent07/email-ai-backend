from typing import Dict
import logging

from authlib.integrations.starlette_client import StarletteOAuth2App
from starlette.requests import Request

from app.infrastructure.auth.google.interface import IGoogleOAuthClient

logger = logging.getLogger(__name__)


class AuthlibGoogleClient(IGoogleOAuthClient):
    """Реализация клиента Google OAuth с использованием Authlib."""

    def __init__(self, google_oauth_client: StarletteOAuth2App = None):
        """Инициализация клиента."""
        self._client = google_oauth_client

    async def get_authorization_url(self, redirect_uri: str, request: Request) -> str:
        """Получение URL для авторизации."""
        logger.info("Starting OAuth authorization process")
        logger.debug(f"Session before redirect: {dict(request.session)}")
        logger.debug(f"State before redirect: {request.session.get('oauth_state')}")
        
        response = await self._client.authorize_redirect(
            request, 
            redirect_uri,
            access_type='offline',  # Для получения refresh_token
            prompt='consent'        # Всегда показывать окно согласия
        )
        
        logger.debug(f"State after redirect: {request.session.get('oauth_state')}")
        logger.debug(f"Session after redirect: {dict(request.session)}")
        logger.info(f"Redirect URL generated: {response.headers['Location']}")
        
        return str(response.headers['Location'])

    async def exchange_code(self, request: Request) -> Dict:
        """Обмен кода авторизации на токены."""
        try:
            logger.info("Starting code exchange")
            logger.debug(f"Session during exchange: {dict(request.session)}")
            logger.debug(f"Request query params: {dict(request.query_params)}")
            
            token = await self._client.authorize_access_token(request)
            logger.info("Access token obtained successfully")
            
            userinfo = await self._client.userinfo(token=token)
            logger.info("User info obtained successfully")
            
            return {
                'access_token': token['access_token'],
                'refresh_token': token.get('refresh_token'),
                'id_token': token.get('id_token'),
                'expires_at': token['expires_at'],
                'userinfo': userinfo
            }
        except Exception as e:
            logger.error(f"Error during code exchange: {str(e)}", exc_info=True)
            raise

    async def refresh_token(self, refresh_token: str) -> Dict:
        """Обновление токена доступа."""
        try:
            logger.info("Starting token refresh")
            token = await self._client.refresh_token(refresh_token)
            logger.info("Token refreshed successfully")
            return {
                'access_token': token['access_token'],
                'refresh_token': token.get('refresh_token')
            }
        except Exception as e:
            logger.error(f"Error during token refresh: {str(e)}", exc_info=True)
            raise

    async def revoke_token(self, token: str) -> None:
        """Отзыв токена доступа."""
        try:
            logger.info("Starting token revocation")
            await self._client.revoke_token(token)
            logger.info("Token revoked successfully")
        except Exception as e:
            logger.error(f"Error during token revocation: {str(e)}", exc_info=True)
            raise

    def create_authorization_url_state(self, request: Request) -> str:
        """Создание уникального состояния для URL авторизации."""
        return self._client.create_authorization_url_state(request)
