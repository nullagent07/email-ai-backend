# app/services/auth_service.py

from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.user_repository import UserRepository
from app.repositories.oauth_credentials_repository import OAuthCredentialsRepository
from app.models.user import User
from app.models.oauth_credentials import OAuthCredentials
from app.core.security import create_access_token
from datetime import datetime, timedelta
from typing import Optional

class OAuthService:
    def __init__(self, db: AsyncSession):
        self.user_repository = UserRepository(db)
        self.oauth_repo = OAuthCredentialsRepository(db)
        self.db = db

    async def authenticate_oauth_user(self, token_data: dict):
        # Извлекаем информацию о пользователе из token_data
        email = token_data.get("email")
        provider = "google"
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")
        expires_in = token_data.get("expires_in")
        name = token_data.get("name")

        # Проверяем, существует ли пользователь
        user = await self.user_repository.get_user_by_email(email)
        is_new_user = False

        if not user:
            # Создаем нового пользователя без пароля
            new_user = User(
                name=name,
                email=email,
                is_subscription_active=False  # По умолчанию
            )
            user = await self.user_repository.create_user(new_user)
            is_new_user = True

        # Обновляем или создаем OAuthCredentials
        oauth_credentials = await self.oauth_repo.get_by_user_id_and_provider(user.id, provider)
        if not oauth_credentials:
            new_credentials = OAuthCredentials(
                user_id=user.id,
                provider=provider,
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=datetime.utcnow() + timedelta(seconds=expires_in),
                email=email
            )
            await self.oauth_repo.create(new_credentials)
        else:
            # Обновляем существующие учетные данные
            oauth_credentials.access_token = access_token
            oauth_credentials.refresh_token = refresh_token
            oauth_credentials.expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            await self.oauth_repo.update(oauth_credentials)

        # Создаем JWT access_token
        token_expires = timedelta(minutes=30)  # Или используйте настройки из конфигурации
        token = create_access_token(data={"sub": str(user.id)}, expires_delta=token_expires)

        return token, is_new_user

    async def get_oauth_credentials_by_email_and_provider(self, email: str, provider: str) -> Optional[OAuthCredentials]:
        """
        Получает OAuth credentials по email пользователя
        
        Args:
            email: Email пользователя
            
        Returns:
            Optional[OAuthCredentials]: Объект с учетными данными или None
        """
        return await self.oauth_repo.get_by_email_and_provider(email, provider)
