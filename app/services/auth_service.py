# app/services/auth_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.oauth_credentials_repository import OAuthCredentialsRepository
from app.models.oauth_credentials import OAuthCredentials
from app.schemas.oauth_credentials_schema import OAuthCredentialsCreate
from typing import Optional

class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.oauth_repo = OAuthCredentialsRepository(db)

    async def link_oauth_credentials(self, oauth_data: OAuthCredentialsCreate) -> OAuthCredentials:
        existing_credentials = await self.oauth_repo.get_by_user_id_and_provider(
            user_id=oauth_data.user_id,
            provider=oauth_data.provider
        )
        if existing_credentials:
            # Обновляем существующие учетные данные
            existing_credentials.access_token = oauth_data.access_token
            existing_credentials.refresh_token = oauth_data.refresh_token
            existing_credentials.expires_at = oauth_data.expires_at
            return await self.oauth_repo.update(existing_credentials)
        else:
            # Создаем новые учетные данные
            new_credentials = OAuthCredentials(
                user_id=oauth_data.user_id,
                provider=oauth_data.provider,
                access_token=oauth_data.access_token,
                refresh_token=oauth_data.refresh_token,
                expires_at=oauth_data.expires_at,
                email=oauth_data.email
            )
            return await self.oauth_repo.create(new_credentials)

    async def get_oauth_credentials(self, user_id: int, provider: str) -> Optional[OAuthCredentials]:
        return await self.oauth_repo.get_by_user_id_and_provider(user_id, provider)

    # Добавьте дополнительные асинхронные методы по необходимости
