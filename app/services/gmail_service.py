# core
from app.core.dependency import get_db
from app.core.config import get_app_settings

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

import Levenshtein
import base64
from email.mime.text import MIMEText


# other 
import base64
import re
from typing import Any
import json
from typing import Union, Optional

settings = get_app_settings()

class GmailService:
    def __init__(self, db: AsyncSession):
        self.db = db

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

    async def send_email(self, gmail, message_body) -> dict:
        """Отправляет email через Gmail API."""
        try:
            return gmail.users().messages().send(userId='me', body=message_body).execute()
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

    async def get_payload_and_headers_and_parts(self, oauth_creds: OAuthCredentials) -> tuple[list[dict], list[dict], list[dict], str, str]: 
        """Получает последнее сообщение"""
        # Создаем gmail сервис
        gmail = await self.create_gmail_service(oauth_creds)

        # Получаем последнее сообщение
        results = gmail.users().messages().list(userId='me', maxResults=1).execute()

        # Формируем массив сообщений
        messages = results.get('messages', [])
        if not messages:
            raise print("No messages found")
        
        # Получаем последнее сообщение
        last_msg_id = messages[0]['id']  
        message = gmail.users().messages().get(userId='me', id=last_msg_id, format='full').execute()
        # Извлекаем thread_id
        gmail_thread_id = message.get('threadId')
        if not gmail_thread_id:
            raise print("Thread ID not found")
        
        # Получаем payload
        payload = message.get('payload', {})

        # Получаем заголовки
        headers = payload.get('headers', [])

        # Извлекаем Message-ID
        message_id_header = None
        subject = "No Subject"
        for header in headers:
            if header['name'] == 'Message-ID':
                message_id_header = header['value']
            if header['name'] == 'Subject':
                subject = header['value']

        # Получаем части
        parts = payload.get('parts', [])

        # Получаем части
        return payload, headers, parts, gmail_thread_id, message_id_header, subject
    
    def normalize_email(self, email):
        """Приведение email к нормальному виду"""
        # Приведение к нижнему регистру
        email = email.lower()
        # Разделяем локальную и доменную части
        local, domain = email.split('@', 1)
        # Удаляем точки только для Gmail
        if 'gmail.com' in domain:
            local = local.replace('.', '')
        return f"{local}@{domain}"

    async def validate_inbox_or_outbox(self, headers: list[dict], user_email: str) -> Union[tuple[str, str], None]:
        """Определяет, является ли сообщение входящим или исходящим"""

        # Инициализация адресов
        from_address = None
        to_address = None

        # Извлекаем значения заголовков 'From' и 'To'
        for header in headers:
            if header['name'] == 'From':
                from_address = header['value']
            elif header['name'] == 'To':
                to_address = header['value']

        if not from_address or not to_address:
            print("Заголовки From или To отсутствуют.")
            return None

        email_pattern = r'([\w\.-]+@[\w\.-]+\.\w+)'  # Регулярное выражение для почты

        try:
            # Извлечение email-адресов
            from_match = re.search(email_pattern, from_address)
            to_match = re.search(email_pattern, to_address)

            if from_match and to_match:
                from_email = from_match.group(1).lower()  # Приведение к нижнему регистру
                to_email = to_match.group(1).lower()
                user_email = user_email.lower()

                # Рассчитываем расстояние Левенштейна для сравнения
                from_distance = Levenshtein.distance(from_email, user_email)
                to_distance = Levenshtein.distance(to_email, user_email)

                # Определяем тип сообщения
                if from_distance == 0:  # Полное совпадение с отправителем
                    print("Это исходящее сообщение.")
                    return None
                elif to_distance == 0:  # Полное совпадение с получателем
                    print("Это входящее сообщение.")
                    return from_email, to_email
                elif from_distance <= 2:  # Допустимая ошибка для отправителя
                    print("Похоже, это исходящее сообщение с опечаткой.")
                    return None
                elif to_distance <= 2:  # Допустимая ошибка для получателя
                    print("Похоже, это входящее сообщение с опечаткой.")
                    return from_email, to_email
                else:
                    print("Невозможно определить тип сообщения.")
                    return None
            else:
                print("Не удалось извлечь email-адреса.")
                return None
        except Exception as e:
            print(f"Ошибка при обработке email-адресов: {str(e)}")
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
        
    def compose_email_body(self, 
                           sender_email: str, 
                           recipient_email: str, 
                           content: str, 
                           subject: str, 
                           thread_id: Optional[str] = None, 
                           references: Optional[str] = None,                            
                           in_reply_to: Optional[str] = None) -> dict:
        """Формирует тело email для отправки через Gmail API."""
        message = MIMEText(content, 'html')
        message['From'] = sender_email
        message['To'] = recipient_email
        message['Subject'] = subject

        if in_reply_to:
            message['In-Reply-To'] = in_reply_to
        if references:
            message['References'] = references
            
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        body = {
        'raw': raw_message
        }
        if thread_id:
            body['threadId'] = thread_id

        return body