from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.exceptions import RefreshError
from fastapi import HTTPException, status
import base64
from app.services.openai_service import OpenAIService
from app.repositories.assistant_profile_repository import AssistantProfileRepository
from app.models.assistant import AssistantProfile
from app.models.email_thread import EmailThread, ThreadStatus
from app.models.user import User
from app.repositories.oauth_credentials_repository import OAuthCredentialsRepository
from app.core.config import get_app_settings
from app.repositories.email_thread_repository import EmailThreadRepository
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.email_thread_schema import EmailThreadCreate
from app.models.email_message import EmailMessage, MessageType
from app.repositories.email_message_repository import EmailMessageRepository
from uuid import UUID
import email.utils
from typing import Any
import json
import httpx
from google.oauth2 import id_token
from google.auth.transport import requests
from google_auth_oauthlib.flow import InstalledAppFlow, Flow
from fastapi import Depends
from app.core.dependency import get_db
from fastapi import Request
from app.repositories.user_repository import UserRepository
from app.services.oauth_service import OAuthService
from app.services.token_service import TokenService
from app.models.oauth_credentials import OAuthCredentials

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

    # async def _save_assistant_and_thread(self, assistant_id: str, openai_thread_id: str, thread_data: EmailThreadCreate) -> EmailThread:
    #     """Сохраняет профиль ассистента и email-тред в базе данных."""
    #     assistant_profile = AssistantProfile(
    #         id=assistant_id,
    #         user_id=thread_data.user_id,
    #         name=thread_data.recipient_name,
    #         description=thread_data.assistant
    #     )
    #     await self.assistant_repo.create_assistant_profile(assistant_profile)
        
    #     new_thread = EmailThread(
    #         id=openai_thread_id,
    #         user_id=thread_data.user_id,
    #         thread_name=thread_data.recipient_name,
    #         description=thread_data.assistant,
    #         status=ThreadStatus.ACTIVE,
    #         assistant_id=assistant_id,
    #         recipient_email=thread_data.recipient_email,
    #         recipient_name=thread_data.recipient_name
    #     )
    #     return await self.thread_repo.create_thread(new_thread)
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
                
            print("Токен успешно проверен")
            print(f"Decoded token: {decoded_token}")
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
    