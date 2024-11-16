# core
from app.core.dependency import get_db
from app.core.config import get_app_settings

# services
from app.services.openai_service import OpenAIService
from app.services.oauth_service import OAuthCredentialsService
from app.services.token_service import TokenService

# repositories
from app.repositories.assistant_profile_repository import AssistantProfileRepository
from app.repositories.oauth_credentials_repository import OAuthCredentialsRepository
from app.repositories.email_thread_repository import EmailThreadRepository
from app.repositories.user_repository import UserRepository

# models
from app.models.oauth_credentials import OAuthCredentials

# google
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.oauth2 import id_token
from google.auth.transport.requests import Request as GoogleRequest
from google_auth_oauthlib.flow import Flow

# fastapi
from fastapi import HTTPException, status, Depends, Request

# sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession

# other 
import base64
import re
from typing import Any
import json
from typing import Union

settings = get_app_settings()

class GmailService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.oauth_repo = OAuthCredentialsRepository(db)
        self.oauth_service = OAuthCredentialsService(db)
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

    async def verify_google_webhook_token(self, token: str) -> bool:
        """
        Проверяет JWT токен Google
        """
        try:
            # Убираем префикс "Bearer"
            token = token.replace("Bearer ", "")
            
            # Создаем правильный объект Request
            request = GoogleRequest()
            
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
    
    async def extract_user_email_from_pubsub_request(self, request: Request):
        # Получаем данные запроса от Pub/Sub
        pubsub_message = await request.json()
        
        # Декодируем данные сообщения
        message_data = pubsub_message['message']['data']
        decoded_data = base64.b64decode(message_data).decode('utf-8')
        email_data = json.loads(decoded_data)
        
        return email_data.get('emailAddress')

    async def get_payload_and_headers_and_parts(self, oauth_creds: OAuthCredentials) -> tuple[list[dict], list[dict], list[dict]]: 
        """Получает последнее сообщение"""
        # Создаем gmail сервис
        gmail = await self.create_gmail_service(oauth_creds)

        # Получаем последнее сообщение
        results = gmail.users().messages().list(userId='me', maxResults=1).execute()

        # Формируем массив сообщений
        messages = results.get('messages', [])

        # Получаем последнее сообщение
        last_msg_id = messages[0]['id']  
        message = gmail.users().messages().get(userId='me', id=last_msg_id, format='full').execute()

        # Получаем payload
        payload = message.get('payload', {})

        # Получаем заголовки
        headers = payload.get('headers', [])

        # Получаем части
        parts = payload.get('parts', [])

        # Получаем части
        return payload, headers, parts

    async def validate_inbox_or_outbox(self, headers: list[dict], user_email: str) -> Union[tuple[str, str], None]:
        """Определяет, является ли сообщение входящим или исходящим"""

        # Извлекаем значения заголовков 'From' и 'To'
        for header in headers:
            if header['name'] == 'From':
                from_address = header['value']
            elif header['name'] == 'To':
                to_address = header['value']

        # Определяем тип сообщения
        if from_address and user_email in from_address:
            print("Это исходящее сообщение.")
            return None
        elif to_address and user_email in to_address:
            print("Это входящее сообщение.")
        else:
            print("Невозможно определить тип сообщения.")
            return None
        
        # Шаблон для извлечения адреса электронной почты
        email_pattern = r'<([^>]+)>'

        # Извлечение адресов с обработкой ошибок
        try:
            from_match = re.search(email_pattern, from_address)
            to_match = re.search(email_pattern, to_address)
            
            if from_match and to_match:
                from_email = from_match.group(1)
                to_email = to_match.group(1)
                return from_email, to_email
        except Exception as e:
            print(f"Ошибка при извлечении адресов: {str(e)}")
        
        return None

    async def get_body_data_from_payload(self, payload: list[dict], parts: list[dict]) -> Union[str, None]:
        """Получает данные из payload"""
        # Получаем данные
        if 'data' in payload.get('body', {}):
            data = payload['body']['data']
        else:
            for part in parts:
                if part.get('mimeType') == 'text/plain' and 'data' in part.get('body', {}):
                    data = part['body']['data']
                break

        # Декодируем данные
        if data:
            decoded_data = base64.urlsafe_b64decode(data).decode('utf-8')
            return decoded_data
        else:
            print(f"Message ID: has no body.")
            return None