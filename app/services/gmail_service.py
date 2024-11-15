from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.exceptions import RefreshError
from fastapi import HTTPException, status, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
import base64

from app.services.openai_service import OpenAIService
from app.services.oauth_service import OAuthService
from app.services.token_service import TokenService

from app.repositories.assistant_profile_repository import AssistantProfileRepository
from app.repositories.oauth_credentials_repository import OAuthCredentialsRepository
from app.repositories.email_thread_repository import EmailThreadRepository
from app.repositories.user_repository import UserRepository
from app.repositories.email_message_repository import EmailMessageRepository


from app.models.assistant_profile import AssistantProfile
from app.models.email_thread import EmailThread, ThreadStatus
from app.models.user import User
from app.models.oauth_credentials import OAuthCredentials
from app.models.email_message import EmailMessage, MessageType

from app.schemas.email_thread_schema import EmailThreadCreate


from uuid import UUID

from typing import Any
import json
import httpx
from google.oauth2 import id_token
from google.auth.transport import requests
from google.auth.transport.requests import Request

from google_auth_oauthlib.flow import InstalledAppFlow, Flow

from app.core.dependency import get_db

from app.core.config import get_app_settings

settings = get_app_settings()

class GmailService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.oauth_repo = OAuthCredentialsRepository(db)
        self.oauth_service = OAuthService(db)
        self.thread_repo = EmailThreadRepository(db)
        self.assistant_repo = AssistantProfileRepository(db)
        self.openai_service = OpenAIService()
        self.user_repository = UserRepository(db)
        self.token_service = TokenService()

    @classmethod
    def get_instance(cls, db: AsyncSession = Depends(get_db)) -> 'GmailService':
        return cls(db)
    
    async def create_oauth_flow(self) -> tuple[str, Flow]:
        """Создает OAuth flow и генерирует URL для авторизации"""
        
        # Создаем конфигурацию клиента
        client_config = {
            "web": {
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.google_redirect_uri]
            }
        }

        # Инициализируем flow
        flow = Flow.from_client_config(
            client_config,
            scopes=settings.google_extended_scope,
            redirect_uri=settings.google_redirect_uri
        )

        return flow
    
    async def create_gmail_service(self, oauth_creds: OAuthCredentials) -> Any:
        """Создает и возвращает сервис Gmail API для пользователя."""
        
        if not oauth_creds:
            raise ValueError("Gmail credentials not found")

        creds = Credentials.from_authorized_user_info({
            "token": oauth_creds.access_token,
            "refresh_token": oauth_creds.refresh_token,
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
        })
        return build('gmail', 'v1', credentials=creds)

    async def send_email(self, gmail, message_body):
        """Отправляет email через Gmail API."""
        try:
            gmail.users().messages().send(userId='me', body=message_body).execute()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to send email: {str(e)}"
            )

    # Обновляем функцию проверки токена вебхука
    async def verify_google_webhook_token(self, token: str) -> bool:
        """
        Проверяет JWT токен Google
        """
        try:
            # Убираем префикс "Bearer"
            token = token.replace("Bearer ", "")
            
            # Создаем правильный объект Request
            request = Request()
            
            # Проверяем JWT токен
            decoded_token = id_token.verify_oauth2_token(
                token,
                request,
                audience=None,  # Позволяем любой audience, так как он динамический (URL ngrok)
                clock_skew_in_seconds=10  # Добавляем допуск по времени
            )
            
            # Проверяем, что токен от нашего сервисного аккаунта
            if decoded_token.get('email') != settings.google_service_account:
                print(f"Неверный email сервисного аккаунта: {decoded_token.get('email')}")
                return False
                
            # Проверяем, что токен не истек
            if 'exp' not in decoded_token:
                print("В токене отсутствует время истечения")
                return False
            
            return True
            
        except Exception as e:
            print(f"Ошибка при проверке токена: {str(e)}")
            return False
        
    async def authenticate_oauth_user(self, token_data: dict):
        # Декодируем id_token и получаем информацию о пользователе
        id_info = id_token.verify_oauth2_token(token_data["id_token"], requests.Request())

        email = id_info.get("email")
        name = id_info.get("name")

        # Проверка существования пользователя
        user = await self.user_repository.get_user_by_email(email)
        is_new_user = False

        if not user:
            new_user = User(name=name, email=email, is_subscription_active=False)
            user = await self.user_repository.create_user(new_user)
            is_new_user = True

        # Обновляем OAuth данные
        await self.oauth_service.update_oauth_credentials(
            user_id=user.id,
            provider="google",
            access_token=token_data.get("access_token"),
            refresh_token=token_data.get("refresh_token"),
            expires_in=token_data.get("expires_in"),
            email=email,
            provider_data={'watch': 'False'}
        )

        # Генерация токена для пользователя
        token = self.token_service.create_access_token(data={"sub": str(user.id)})

        return token, is_new_user
    