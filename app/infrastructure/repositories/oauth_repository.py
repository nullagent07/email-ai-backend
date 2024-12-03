from app.domain.models.oauth import OAuthCredentials

class OAuthRepository:
    """Репозиторий для работы с таблицей OAuth учетных данных."""

    def add_credentials(self, credentials_data: dict) -> OAuthCredentials:
        """Добавляет новые OAuth учетные данные в базу данных."""
        # Здесь добавьте логику для добавления учетных данных в базу данных
        print("Добавление OAuth учетных данных в базу данных:", credentials_data)
        return OAuthCredentials(**credentials_data)

    def get_credentials_by_email(self, email: str) -> OAuthCredentials:
        """Получает OAuth учетные данные по email."""
        # Здесь добавьте логику для получения учетных данных из базы данных
        print("Получение OAuth учетных данных по email:", email)
        return OAuthCredentials(email=email)
