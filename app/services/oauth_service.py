# app/services/auth_service.py

# sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession
# repositories
from app.repositories.user_repository import UserRepository
from app.repositories.oauth_credentials_repository import OAuthCredentialsRepository
# models
from app.models.user import User
from app.models.oauth_credentials import OAuthCredentials
# services
from app.services.token_service import TokenService
# other
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends
from app.core.dependency import get_db
from google.oauth2 import id_token
from google.auth.transport import requests
from fastapi import HTTPException



class OAuthService:
    def __init__(self, db: AsyncSession):
        self.user_repository = UserRepository(db)
        self.oauth_repo = OAuthCredentialsRepository(db)
        self.token_service = TokenService()
        self.db = db

    @classmethod
    def get_instance(cls, db: AsyncSession = Depends(get_db)) -> 'OAuthService':
        return cls(db)

    async def authenticate_oauth_user(self, token_data: dict):
    # Декодируем id_token и получаем информацию о пользователе
        id_info = id_token.verify_oauth2_token(token_data["id_token"], requests.Request())

        print(f"ID info: {id_info}")
        email = id_info.get("email")
        name = id_info.get("name")

        # Другие параметры из token_data
        access_token = token_data.get("access_token")
        refresh_token = token_data.get("refresh_token")
        expires_in = token_data.get("expires_in")

        # Проверка существования пользователя
        user = await self.user_repository.get_user_by_email(email)
        is_new_user = False

        if not user:
            new_user = User(name=name, email=email, is_subscription_active=False)
            user = await self.user_repository.create_user(new_user)
            is_new_user = True

        # Обновление OAuth данных
        oauth_credentials = await self.oauth_repo.get_by_user_id_and_provider(user.id, "google")
        if not oauth_credentials:
            expires_at = expires_in if isinstance(expires_in, datetime) else datetime.utcnow() + timedelta(seconds=expires_in)
            new_credentials = OAuthCredentials(
                user_id=user.id,
                provider="google",
                access_token=access_token,
                refresh_token=refresh_token,
                expires_at=expires_at,
                email=email
            )
            await self.oauth_repo.create(new_credentials)
        else:
            # Если expires_in — `datetime`, устанавливаем его напрямую, иначе — добавляем к текущему времени
            oauth_credentials.expires_at = expires_in if isinstance(expires_in, datetime) else datetime.utcnow() + timedelta(seconds=expires_in)
            await self.oauth_repo.update(oauth_credentials)

        # Генерация токена для пользователя
        token = self.token_service.create_access_token(data={"sub": str(user.id)})

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
