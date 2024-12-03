from app.infrastructure.repositories.oauth_repository import OAuthRepository
from app.domain.models.oauth import OAuthCredentials

class OAuthService:
    """Сервис для работы с OAuth учетными данными."""

    def __init__(self, oauth_repository: OAuthRepository):
        self.oauth_repository = oauth_repository

    def create_credentials(self, credentials_data: dict) -> OAuthCredentials:
        """Создает новые OAuth учетные данные."""
        return self.oauth_repository.add_credentials(credentials_data)

    def find_credentials_by_email(self, email: str) -> OAuthCredentials:
        """Находит OAuth учетные данные по email."""
        # Логика поиска учетных данных по email может быть добавлена здесь
        print("Поиск OAuth учетных данных по email:", email)
        return self.oauth_repository.get_credentials_by_email(email)
