from app.applications.services.user_service import UserService
from app.applications.services.oauth_service import OAuthService
from app.domain.models.user import User
from app.domain.models.oauth import OAuthCredentials

class AuthOrchestrator:
    """Оркестратор для управления процессом аутентификации."""

    def __init__(self, user_service: UserService, oauth_service: OAuthService):
        self.user_service = user_service
        self.oauth_service = oauth_service

    def google_authenticate(self, auth_result: dict) -> User:
        """Аутентифицирует пользователя через Google и обновляет или создает учетные записи."""
        userinfo = auth_result['userinfo']
        email = userinfo['email']

        # Проверяем, существует ли пользователь
        user = self.user_service.find_user_by_email(email)
        if not user:
            # Создаем нового пользователя
            user = self.user_service.create_user({
                'name': userinfo['name'],
                'email': email
            })

        # Обновляем или создаем учетные данные OAuth
        self.oauth_service.create_credentials({
            'user_id': user.id,
            'provider': 'google',
            'access_token': auth_result['access_token'],
            'refresh_token': auth_result['refresh_token'],
            'expires_at': auth_result.get('expires_at'),
            'email': email,
            'provider_data': userinfo
        })

        return user
