# app/services/email_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.repositories.email_message_repository import EmailMessageRepository
from app.repositories.email_thread_repository import EmailThreadRepository
from app.models.email_message import EmailMessage, MessageType
from app.models.email_thread import EmailThread, ThreadStatus
from app.schemas.email_message_schema import EmailMessageCreate
from app.schemas.email_thread_schema import EmailThreadCreate, EmailThreadUpdate
from typing import Optional
from app.services.openai_service import OpenAIService
from app.repositories.assistant_repository import AssistantRepository
from app.models.assistant import AssistantProfile
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from app.core.config import settings
import base64
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from fastapi import HTTPException, status
from app.repositories.oauth_credentials_repository import OAuthCredentialsRepository

class EmailService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.message_repo = EmailMessageRepository(db)
        self.thread_repo = EmailThreadRepository(db)
        self.assistant_repo = AssistantRepository(db)
        self.oauth_repo = OAuthCredentialsRepository(db)
        self.openai_service = OpenAIService()

    # Методы для EmailThread
    async def create_email_thread(self, thread_data: EmailThreadCreate) -> EmailThread:

        # 1. Получаем OAuth credentials для Gmail
        # oauth_repo = OAuthCredentialsRepository(self.db)
        oauth_creds = await self.oauth_repo.get_by_user_id_and_provider(
            thread_data.user_id, 
            "google"
        )

        if not oauth_creds:
            raise ValueError("Gmail credentials not found")

        # 2. Создаем тред в OpenAI с начальным сообщением
        openai_thread_id, initial_message = await self.openai_service.create_thread_with_initial_message(
            name=thread_data.name,
            description=thread_data.assistant_description
        )
        
        # 3. Отправляем email через Gmail API
        message = {
            'raw': base64.urlsafe_b64encode(
                f"""From: {oauth_creds.email}\r\n\
To: {thread_data.email}\r\n\
Subject: New conversation with {thread_data.name}\r\n\
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

            # print("creds", creds)
            
            service = build('gmail', 'v1', credentials=creds)
            service.users().messages().send(userId="me", body=message).execute()
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to send email: {str(e)}"
            )
        
        # 4. Создаем email тред в базе
        new_thread = EmailThread(
            user_id=thread_data.user_id,
            thread_name=thread_data.thread_name,
            description=thread_data.description,
            status=ThreadStatus.ACTIVE,
            openai_thread_id=openai_thread_id
        )
        thread = await self.thread_repo.create_thread(new_thread)
        
        # 5. Сохраняем профиль ассистента в базе
        assistant_profile = AssistantProfile(
            user_id=thread_data.email,
            name=thread_data.name,
            description=thread_data.assistant_description,
            thread_id=thread.id
        )
        await self.assistant_repo.create_assistant_profile(assistant_profile)
        
        return thread

    async def get_user_threads(self, user_id: int) -> List[EmailThread]:
        return await self.thread_repo.get_threads_by_user_id(user_id)

    async def close_email_thread(self, thread_id: int) -> EmailThread:
        thread = await self.thread_repo.get_thread_by_id(thread_id)
        if not thread:
            raise ValueError("Thread not found")
        thread.status = ThreadStatus.CLOSED
        return await self.thread_repo.update_thread(thread)

    async def get_threads_by_status(self, user_id: int, status: ThreadStatus) -> List[EmailThread]:
        return await self.thread_repo.get_threads_by_status(user_id, status)

    # Методы для EmailMessage
    async def send_email_message(self, message_data: EmailMessageCreate) -> EmailMessage:
        new_message = EmailMessage(
            thread_id=message_data.thread_id,
            message_type=MessageType.OUTGOING,
            subject=message_data.subject,
            content=message_data.content,
            sender_email=message_data.sender_email,
            recipient_email=message_data.recipient_email
        )
        # Здесь можно добавить асинхронный код для отправки email
        return await self.message_repo.create_message(new_message)

    async def receive_email_message(self, message_data: EmailMessageCreate) -> EmailMessage:
        new_message = EmailMessage(
            thread_id=message_data.thread_id,
            message_type=MessageType.INCOMING,
            subject=message_data.subject,
            content=message_data.content,
            sender_email=message_data.sender_email,
            recipient_email=message_data.recipient_email
        )
        # Здесь можно добавить асинхронный код для обработки входящего email
        return await self.message_repo.create_message(new_message)

    async def get_messages_in_thread(self, thread_id: int) -> List[EmailMessage]:
        return await self.message_repo.get_messages_by_thread_id(thread_id)

    async def get_message_by_id(self, message_id: int) -> Optional[EmailMessage]:
        return await self.message_repo.get_message_by_id(message_id)

    # Добавьте дополнительные асинхронные методы по необходимости
