from app.infrastructure.repositories.oauth_repository import OAuthRepository
from app.domain.models.oauth import OAuthCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.interfaces.services.oauth_service_interface import IOAuthService
from app.domain.interfaces.repositories.oauth_repository_interface import IOAuthRepository

class OAuthService(IOAuthService):
    """Сервис для работы с OAuth учетными данными."""

    def __init__(self, db_session: AsyncSession):        
        self.oauth_repository : IOAuthRepository = OAuthRepository(db_session=db_session)

    async def create_credentials(self, credentials_data: dict) -> OAuthCredentials:
        """Создает новые OAuth учетные данные."""
        return await self.oauth_repository.add_credentials(credentials_data)

    async def find_credentials_by_email(self, email: str) -> OAuthCredentials:
        """Находит OAuth учетные данные по email."""
        # Логика поиска учетных данных по email может быть добавлена здесь
        print("Поиск OAuth учетных данных по email:", email)
        return await self.oauth_repository.get_credentials_by_email(email)
