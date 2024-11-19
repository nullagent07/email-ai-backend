# app/services/gmail_service.py

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request
from google.oauth2 import id_token
from fastapi import HTTPException, status, Depends
from fastapi.requests import Request

import asyncio
import time
from typing import Any, Dict, Optional
from datetime import datetime
from collections import defaultdict

from app.core.config import get_app_settings
from app.core.dependency import get_db
from app.models.oauth_credentials import OAuthCredentials
from app.services.oauth_service import OAuthCredentialsService
from app.services.open_ai_service import OpenAIService
from app.services.token_service import TokenService
from app.services.user_service import UserService

from app.schemas.email_thread_schema import EmailThreadCreate
from app.core.dependency import get_db

from sqlalchemy.ext.asyncio import AsyncSession
import base64
import re
from email.mime.text import MIMEText
import json
import Levenshtein
from typing import Union


settings = get_app_settings()

class GmailService:
    _instance = None
    _lock = asyncio.Lock()
    
    def __init__(self):
        self.settings = get_app_settings()
        self._flows = {}
        self._request_counts = defaultdict(int)
        self._last_request_times = defaultdict(float)
        self._cleanup_task = None
        self._rate_limit_lock = asyncio.Lock()  # Добавляем отдельный lock для rate limiting
        
        # Настройки rate limiting
        self.MAX_REQUESTS_PER_SECOND = 10
        self.MAX_CONCURRENT_FLOWS = 50
        self.MIN_REQUEST_INTERVAL = 0.1  # 100ms
        self.FLOW_TIMEOUT = 300  # 5 минут
        
    @classmethod
    async def get_instance(cls):
        if not cls._instance:
            async with cls._lock:
                if not cls._instance:
                    cls._instance = cls()
                    cls._instance._cleanup_task = asyncio.create_task(cls._instance._cleanup_expired_flows())
        return cls._instance

    async def _check_rate_limit(self, client_ip: str) -> None:
        """Проверка rate limit для клиента"""
        async with self._rate_limit_lock:  # Используем lock для защиты от race conditions
            current_time = time.time()
            
            # Проверяем и сбрасываем счетчик, если прошла секунда
            last_request_time = self._last_request_times[client_ip]
            if current_time - last_request_time >= 1.0:  # Если прошла секунда
                self._request_counts[client_ip] = 0  # Сбрасываем счетчик
            
            # Проверяем интервал между запросами
            if current_time - last_request_time < self.MIN_REQUEST_INTERVAL:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Request rate exceeded. Please wait before trying again."
                )
            
            # Проверяем количество запросов в секунду
            if self._request_counts[client_ip] >= self.MAX_REQUESTS_PER_SECOND:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many requests per second. Please slow down."
                )
            
            # Проверяем количество активных flows
            if len(self._flows) >= self.MAX_CONCURRENT_FLOWS:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Maximum number of concurrent authentication flows reached. Please try again later."
                )
            
            # Обновляем счетчики
            self._request_counts[client_ip] += 1
            self._last_request_times[client_ip] = current_time
            
            # Запускаем асинхронную задачу для сброса счетчика
            asyncio.create_task(self._reset_request_count(client_ip))

    async def _reset_request_count(self, client_ip: str):
        """Сбрасывает счетчик запросов через секунду"""
        await asyncio.sleep(1)
        async with self._rate_limit_lock:
            if client_ip in self._request_counts:
                self._request_counts[client_ip] = max(0, self._request_counts[client_ip] - 1)

    async def cleanup_flow(self, client_ip: str) -> None:
        """Очищает ресурсы flow для клиента"""
        async with self._rate_limit_lock:
            if client_ip in self._flows:
                del self._flows[client_ip]
            if client_ip in self._request_counts:
                del self._request_counts[client_ip]
            if client_ip in self._last_request_times:
                del self._last_request_times[client_ip]

    async def create_oauth_flow(self, client_ip: str) -> InstalledAppFlow:
        """Создает новый OAuth flow для клиента"""
        await self._check_rate_limit(client_ip)
        
        try:
            client_config = {
                "installed": {
                    "client_id": self.settings.google_client_id,
                    "client_secret": self.settings.google_client_secret,
                    "redirect_uris": [self.settings.google_redirect_uri],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs"
                }
            }
            print(f"Client config: {client_config}")
            
            flow = InstalledAppFlow.from_client_config(
                client_config,
                scopes=self.settings.google_extended_scope,
                redirect_uri=self.settings.google_redirect_uri
            )
            
            self._flows[client_ip] = {
                "flow": flow,
                "created_at": time.time()
            }
            return flow
            
        except Exception as e:
            print(f"Error creating OAuth flow: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Failed to create authentication flow. Please try again later."
            )

    async def create_gmail_service(self, oauth_creds: OAuthCredentials) -> Any:
        """Создает и возвращает сервис Gmail API для пользователя."""
        
        if not oauth_creds:
            raise ValueError("Gmail credentials not found")

        creds = Credentials.from_authorized_user_info({
            "token": oauth_creds.access_token,
            "refresh_token": oauth_creds.refresh_token,
            "client_id": self.settings.google_client_id,
            "client_secret": self.settings.google_client_secret,
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
            request = Request()
            
            # Проверяем JWT токен
            decoded_token = id_token.verify_oauth2_token(
                token,
                request,
                audience=None,  # Позволяем любой audience, так как он динамический (URL ngrok)
                clock_skew_in_seconds=10  # Добавляем допуск по времени
            )
            
            # Проверяем, что токен от нашего сервисного аккаунта
            if decoded_token.get('email') != self.settings.google_service_account:
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

    async def get_payload_and_headers_and_parts(self, oauth_creds: OAuthCredentials) -> tuple[list[dict], list[dict], list[dict], str, str, str]: 
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

    async def validate_inbox_or_outbox(self, 
                                       headers: list[dict], 
                                       user_email: str) -> Union[tuple[str, str], None]:
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
        
    async def get_body_data_from_payload(self,
                                        payload: list[dict], 
                                        parts: list[dict]) -> Union[str, None]:
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
    
    async def is_watch_active(self, oauth_creds: OAuthCredentials) -> bool:
        """Проверяет, есть ли активный watch для конкретного пользователя в Google проекте."""
        try:
            if not oauth_creds:
                raise ValueError("OAuth credentials not found for the user")

            # Создаем Gmail сервис
            gmail = await self.create_gmail_service(oauth_creds)

            # Получаем информацию о текущем watch
            watch_response = gmail.users().watch().get(userId='me').execute()

            # Проверяем наличие активного watch
            return bool(watch_response.get('historyId'))

        except Exception as e:
            print(f"Error checking watch status for {oauth_creds.email}: {e}")
            return False
    
    async def create_watch(self, oauth_creds: OAuthCredentials) -> None:
        """Создает watch для пользователя, если он не активен."""
        try:
            # Создаем Gmail сервис
            gmail = await self.create_gmail_service(oauth_creds)

            # Настраиваем watch запрос
            watch_request = {
                'labelIds': ['INBOX'],
                'topicName': f'projects/{self.settings.google_project_id}/topics/{self.settings.google_topic_id}'
            }

            # Отправляем watch запрос
            gmail.users().watch(userId='me', body=watch_request).execute()
            print(f"Watch успешно создан для {oauth_creds.email}")

        except Exception as e:
            print(f"Ошибка при создании watch для {oauth_creds.email}: {e}")

    async def delete_watch(self, oauth_creds: OAuthCredentials) -> None:
        """Удаляет watch для кон��ретного пользователя."""
        try:
            # Создаем Gmail сервис
            gmail = await self.create_gmail_service(oauth_creds)

            # Отправляем запрос на удаление watch
            gmail.users().stop(userId='me').execute()
            print(f"Watch успешно удален для {oauth_creds.email}")

        except Exception as e:
            print(f"Ошибка при удалении watch для {oauth_creds.email}: {e}")

    async def _cleanup_expired_flows(self) -> None:
        """Периодически очищает устаревшие flows"""
        while True:
            try:
                current_time = time.time()
                async with self._rate_limit_lock:
                    # Очищаем устаревшие flows
                    expired_ips = [
                        ip for ip, (flow, timestamp) in self._flows.items()
                        if current_time - timestamp > self.FLOW_TIMEOUT
                    ]
                    for ip in expired_ips:
                        del self._flows[ip]
                        if ip in self._request_counts:
                            del self._request_counts[ip]
                        if ip in self._last_request_times:
                            del self._last_request_times[ip]
                
                # Ждем 60 секунд перед следующей проверкой
                await asyncio.sleep(60)
            except Exception as e:
                print(f"Error in cleanup task: {e}")
                await asyncio.sleep(60)  # В случае ошибки тоже ждем 60 секунд