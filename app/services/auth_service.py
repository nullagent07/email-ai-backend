from datetime import datetime, timedelta
from fastapi import HTTPException, status
from app.repositories.auth_repository import AuthRepository
from app.schemas.auth import OAuthUser, OAuthCredentials
from app.core import security
import bcrypt
from jose import JWTError, jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from app.core.config import get_app_settings
from app.models.user import User  
from sqlalchemy.ext.asyncio import AsyncSession
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

settings = get_app_settings()

class AuthService:
    def __init__(self, repository: AuthRepository):
        self._repository = repository
    
    async def authenticate_oauth_user(self, token_data: dict) -> tuple[str, bool]:
        """
        Аутентифицирует или создает пользователя через OAuth
        Возвращает: (access_token, is_new_user)
        """
        oauth_creds = await self._repository.get_oauth_credentials(
            email=token_data["email"],
            provider="google"
        )
        
        if oauth_creds:
            # Используем сессию из репозитория
            user = await self._repository.session.get(User, oauth_creds.user_id)
            # Обновляем существующие credentials
            expires_at = datetime.utcnow() + timedelta(seconds=token_data["expires_in"])
            await self._repository.update_oauth_credentials(
                credentials=oauth_creds,
                access_token=token_data["access_token"],
                refresh_token=token_data.get("refresh_token"),
                expires_at=expires_at
            )
            is_new_user = False
        else:
            # Создаем нового пользователя
            user_data = OAuthUser(
                email=token_data["email"],
                name=token_data.get("name", token_data["email"].split("@")[0]),
                is_subscription_active=False
            )
            
            credentials_data = OAuthCredentials(
                provider="google",
                email=token_data["email"],
                access_token=token_data["access_token"],
                refresh_token=token_data.get("refresh_token"),
                expires_at=datetime.utcnow() + timedelta(seconds=token_data["expires_in"])
            )
            
            user = await self._repository.create_user_with_oauth(
                user_data=user_data,
                credentials_data=credentials_data
            )
            is_new_user = True
            
        return security.create_access_token(user.id), is_new_user

    async def set_password(self, user_id: int, password: str) -> bool:
        """
        Устанавливает пароль для пользователя
        """
        password_hash = self._get_password_hash(password)
        user = await self._repository.update_user_password(user_id, password_hash)
        return bool(user)

    def _get_password_hash(self, password: str) -> str:
        """
        Создает хэш пароля используя, например, bcrypt
        """
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    async def refresh_google_token(self, oauth_creds: OAuthCredentials) -> dict:
        """Обновляет Google токен используя refresh_token"""
        if not oauth_creds.refresh_token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No refresh token available"
            )
        
        creds = Credentials(
            token=oauth_creds.access_token,
            refresh_token=oauth_creds.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.google_client_id,
            client_secret=settings.google_client_secret,
            scopes=[
                'https://www.googleapis.com/auth/gmail.readonly',
                'https://www.googleapis.com/auth/gmail.send'
            ]
        )
        
        request = Request()
        creds.refresh(request)
        
        # Обновляем токены в базе
        expires_at = datetime.utcnow() + timedelta(seconds=3600)
        await self._repository.update_oauth_credentials(
            credentials=oauth_creds,
            access_token=creds.token,
            refresh_token=creds.refresh_token,
            expires_at=expires_at
        )
        
        return {
            'valid': True,
            'access_token': creds.token,
            'expires_in': 3600
        }