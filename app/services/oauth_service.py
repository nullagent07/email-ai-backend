# app/services/auth_service.py

# sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession

# repositories
from app.repositories.oauth_credentials_repository import OAuthCredentialsRepository

# models
from app.models.oauth_credentials import OAuthCredentials

# core
from app.core.dependency import get_db

# other
from datetime import datetime, timedelta
from typing import Optional, Union
from fastapi import Depends
from uuid import UUID



class OAuthCredentialsService:
    def __init__(self, db: AsyncSession):
        self.oauth_credentials_repo = OAuthCredentialsRepository(db)
        self.db = db

    @classmethod
    def get_instance(cls, db: AsyncSession = Depends(get_db)) -> 'OAuthCredentialsService':
        return cls(db)
    
    async def get_oauth_credentials_by_user_id_and_provider(self, user_id: UUID, provider: str) -> Optional[OAuthCredentials]:
        """Получает OAuth credentials по user_id и provider"""
        return await self.oauth_credentials_repo.get_by_user_id_and_provider(user_id, provider) 

    async def update_oauth_credentials(
        self, 
        user_id: int, 
        provider: str,
        access_token: str,
        refresh_token: str,
        expires_in: Union[datetime, int],
        email: str,
        provider_data: dict
    ) -> None:
        """Обновляет или создает OAuth учетные данные пользователя"""
        oauth_credentials = await self.get_oauth_credentials_by_user_id_and_provider(user_id, provider)

        if not oauth_credentials:
            expires_at = expires_in if isinstance(expires_in, datetime) else datetime.utcnow() + timedelta(seconds=expires_in)
            new_credentials = OAuthCredentials(
                user_id=user_id,
                provider=provider,
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=expires_at,
                email=email,
                provider_data=provider_data
            )
            await self.oauth_credentials_repo.create(new_credentials)
        else:
            oauth_credentials.expires_at = expires_in if isinstance(expires_in, datetime) else datetime.utcnow() + timedelta(seconds=expires_in)
            oauth_credentials.access_token = access_token
            if refresh_token:  # Обновляем refresh_token только если он предоставлен
                oauth_credentials.refresh_token = refresh_token
            await self.oauth_credentials_repo.update(oauth_credentials)

    async def get_oauth_credentials_by_email_and_provider(self, email: str, provider: str) -> Optional[OAuthCredentials]:
        """
        Получает OAuth credentials по email пользователя
        
        Args:
            email: Email пользователя
            
        Returns:
            Optional[OAuthCredentials]: Объект с учетными данными или None
        """
        return await self.oauth_credentials_repo.get_by_email_and_provider(email, provider)
