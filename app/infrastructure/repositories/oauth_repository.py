from app.domain.models.oauth import OAuthCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.interfaces.repositories.oauth_repository_interface import IOAuthRepository


class OAuthRepository(IOAuthRepository):
    """Репозиторий для работы с таблицей OAuth учетных данных."""

    def __init__(self, db_session: AsyncSession) -> None:
        self.db_session = db_session

    async def add_credentials(self, credentials_data: dict) -> OAuthCredentials:
        """Добавляет новые OAuth учетные данные в базу данных."""
        async with self.db_session.begin():
            new_credentials = OAuthCredentials(**credentials_data)
            self.db_session.add(new_credentials)
            await self.db_session.commit()
            return new_credentials

    async def get_credentials_by_email(self, email: str) -> OAuthCredentials:
        """Получает OAuth учетные данные по email."""
        async with self.db_session.begin():
            result = await self.db_session.execute(
                select(OAuthCredentials).where(OAuthCredentials.email == email)
            )
            return result.scalar_one_or_none()

    async def update_credentials(self, email: str, provider: str, credentials_data: dict) -> OAuthCredentials:
        """Обновляет существующие OAuth учетные данные в базе данных для конкретного провайдера."""
        async with self.db_session.begin():
            result = await self.db_session.execute(
                select(OAuthCredentials).where(
                    OAuthCredentials.email == email,
                    OAuthCredentials.provider == provider
                )
            )
            credentials = result.scalar_one_or_none()
            if credentials:
                for key, value in credentials_data.items():
                    setattr(credentials, key, value)
                await self.db_session.commit()
                return credentials
            return None
