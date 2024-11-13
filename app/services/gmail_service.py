from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from google.auth.exceptions import RefreshError
from fastapi import HTTPException, status
import base64
from app.services.openai_service import OpenAIService
from app.repositories.assistant_repository import AssistantRepository
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
# from app.utils.oauth_verification import verify_google_webhook_token
from fastapi import Depends
from app.core.dependency import get_db
from fastapi import Request
from app.repositories.user_repository import UserRepository
from app.services.oauth_service import OAuthService
from app.services.token_service import TokenService
settings = get_app_settings()

class GmailService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.oauth_repo = OAuthCredentialsRepository(db)
        self.oauth_service = OAuthService(db)
        self.thread_repo = EmailThreadRepository(db)
        self.assistant_repo = AssistantRepository(db)
        self.openai_service = OpenAIService()
        self.message_repo = EmailMessageRepository(db)
        self.user_repository = UserRepository(db)
        self.token_service = TokenService()
        self.processed_messages = set()

    @classmethod
    def get_instance(cls, db: AsyncSession = Depends(get_db)) -> 'GmailService':
        return cls(db)
    
    async def authenticate_oauth_user(self, token_data: dict):
        # Декодируем id_token и получаем информацию о пользователе
        id_info = id_token.verify_oauth2_token(token_data["id_token"], requests.Request())

        print(f"ID info: {id_info}")
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
            email=email
        )

        # Генерация токена для пользователя
        token = self.token_service.create_access_token(data={"sub": str(user.id)})

        return token, is_new_user
        
    async def setup_email_monitoring(self, user_id: UUID) -> None:
        try:
            oauth_creds = await self.oauth_repo.get_by_user_id_and_provider(user_id, "google")
            if not oauth_creds:
                raise ValueError("Gmail credentials not found")

            creds = Credentials.from_authorized_user_info(
                info={
                    "token": oauth_creds.access_token,
                    "refresh_token": oauth_creds.refresh_token,
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                }
            )
            
            service = build('gmail', 'v1', credentials=creds)
            
            topic_name = f"projects/{settings.google_project_id}/topics/{settings.google_topic_id}"
            
            request = {
                'labelIds': ['INBOX'],
                'topicName': topic_name,
                'labelFilterAction': 'include'
            }
            
            try:
                response = service.users().watch(userId='me', body=request).execute()
                print(f"Watch response: {response}")
                return response
            except Exception as e:
                print(f"Watch request failed: {str(e)}")
                raise
            
        except Exception as e:
            print(f"Error in setup_email_monitoring: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to setup email monitoring: {str(e)}"
            )
    
    async def create_gmail_thread(self, thread_data: EmailThreadCreate) -> EmailThread:
        # 1. Получаем OAuth credentials для Gmail
        oauth_creds = await self.oauth_repo.get_by_user_id_and_provider(
            thread_data.user_id, 
            "google"
        )

        if not oauth_creds:
            raise ValueError("Gmail credentials not found")

        # 2. Создаем ассистента в OpenAI с подробными инструкциями
        assistant_id = await self.openai_service.create_assistant(
            name=f"Email Assistant for {thread_data.recipient_name}",
            instructions=f"""Ты - умный email ассистент, который помогает вести переписку с {thread_data.recipient_name}.
            
            Формат письма (испоьзуй HTML-теги):
            1. Базовая структур:
               <div style="margin-bottom: 20px">Приветствие</div>
               
               <div style="margin-bottom: 15px; text-indent: 20px">Первый абзац основной части</div>
               
               <div style="margin-bottom: 15px; text-indent: 20px">Второй абзац основной части</div>
               
               <div style="margin-bottom: 20px; text-indent: 20px">Заключительный абзац</div>
               
               <div style="margin-top: 30px">С уважением,<br>
               [Подпись]</div>
            
            2. Правила форматирования:
               • Каждый абзац оборачивай в <div> с отступами
               • Используй <br> для переноса строк
               • Для списков используй <ul> и <li>
               • Важные части можно выделить <strong>
            
            3. Прмер структуры:
            
            <div style="margin-bottom: 20px">
            Уважаемый {thread_data.recipient_name}!
            </div>
            
            <div style="margin-bottom: 15px; text-indent: 20px">
            Надеюсь, это письмо найдет Вас в добром здравии. [Оcновная мысль первого абзаца...]
            </div>
            
            <div style="margin-bottom: 15px; text-indent: 20px">
            [Второй абзац с отступом...]
            </div>
            
            <div style="margin-bottom: 20px; text-indent: 20px">
            [Заключительный абзац с отступом...]
            </div>
            
            <div style="margin-top: 30px">
            С уважением,<br>
            [Подпись]
            </div>
            
            Дополнительный контект:
            {thread_data.assistant}
            """
        )

        # 3. Создаем тред в OpenAI
        openai_thread_id = await self.openai_service.create_thread()

        # 4. Добавляем начальное сообщение в тред
        await self.openai_service.add_message_to_thread(
            thread_id=openai_thread_id,
            content=f"""Это начало email переписки с {thread_data.recipient_name}.
            
            Напиши первое приветственное письмо, учитывая следующий контекст:
            {thread_data.assistant}
            
            Письмо должно:
            1. Начинаться с приветствия
            2. Представить себя как описано в контексте
            3. Объяснить цель переписки
            4. Закончиться вежливой подписью
            """
        )

        # 5. Проверяем суествование ассистента
        assistant = await self.openai_service.get_assistant(assistant_id)
        if not assistant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Assistant not found"
            )

        # 6. Запускаем ассистента и получаем ответ с обработкой ошибок
        try:
            initial_message = await self.openai_service.run_thread(
                thread_id=openai_thread_id,
                assistant_id=assistant_id,
                instructions="""
                Сгенерируй приветственное письмо, учитывая:
                1. Имя получателя
                2. Контекст переписки
                3. Деловой стиль
                """,
                timeout=30.0  # таймаут
            )
            
            if initial_message is None:
                # Очищаем ресурсы при ошибке
                await self.openai_service.delete_assistant(assistant_id)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to generate initial message"
                )
                
        except Exception as e:
            # Очищаем ресурсы при ошибке
            await self.openai_service.delete_assistant(assistant_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error running thread: {str(e)}"
            )

        # 7. Отправляем email через Gmail API
        message = {
            'raw': base64.urlsafe_b64encode(
                f"""From: {oauth_creds.email}\r\n\
To: {thread_data.recipient_email}\r\n\
Subject: New conversation with {thread_data.recipient_name}\r\n\
MIME-Version: 1.0\r\n\
Content-Type: text/html; charset=utf-8\r\n\
\r\n\
{initial_message}""".encode()
            ).decode()
        }

        try:
            # Создаем сервис Gmail API используя существующий токен
            creds = Credentials.from_authorized_user_info(
                info={
                    "token": oauth_creds.access_token,
                    "refresh_token": oauth_creds.refresh_token,
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                },
            )
            
            service = build('gmail', 'v1', credentials=creds)
            service.users().messages().send(userId="me", body=message).execute()
            
            # Настраиваем мониторинг писем для созданного треда
            await self.setup_email_monitoring(thread_data.user_id)
            
        except Exception as e:
            # В случае ошибки удаляем созданного ассистента
            await self.openai_service.delete_assistant(assistant_id)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to send email: {str(e)}"
            )
        
        # 7. Создаем профиль ассистента в базе
        assistant_profile = AssistantProfile(
            id=assistant_id,
            user_id=thread_data.user_id,
            name=thread_data.recipient_name,
            description=thread_data.assistant
        )
        await self.assistant_repo.create_assistant_profile(assistant_profile)
        
        # 8. Создаем email тред в базе
        new_thread = EmailThread(
            id=openai_thread_id,
            user_id=thread_data.user_id,
            thread_name=thread_data.recipient_name,
            description=thread_data.assistant,
            status=ThreadStatus.ACTIVE,
            assistant_id=assistant_id,
            recipient_email=thread_data.recipient_email,
            recipient_name=thread_data.recipient_name
        )
        thread = await self.thread_repo.create_thread(new_thread)
        
        return thread

    async def create_gmail_service(self, email_address: str) -> Any:
        """
        Создает и возвращает сервис Gmail API
        
        Args:
            user_id: ID пользователя
            
        Returns:
            service: Объект сервиса Gmail API
            
        Raises:
            ValueError: Если не найдены учетные данные OAuth
        """
        # Получаем OAuth credentials
        oauth_creds = await self.oauth_repo.get_by_email_and_provider(
            email_address, 
            "google"
        )
        
        if not oauth_creds:
            raise ValueError("Gmail credentials not found")
            
        # Создаем сервис Gmail API
        creds = Credentials.from_authorized_user_info(
            info={
                "token": oauth_creds.access_token,
                "refresh_token": oauth_creds.refresh_token,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
            }
        )
        
        return build('gmail', 'v1', credentials=creds)

    # Обновляем функцию проверки токена вебхука
    async def verify_google_webhook_token(self, token: str) -> bool:
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