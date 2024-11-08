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
            
            Основные правила:
            1. Всегда пиши в деловом, но дружелюбном тоне
            2. Используй обращение по имени: {thread_data.recipient_name}
            3. Подписывайся в конце каждого письма
            4. Следи за контекстом всей переписки
            5. Если не уверен в чем-то, задавай уточняющие вопросы
            6. Всегда форматируй текст для email (с приветствием и подписью)
            
            Дополнительный контекст:
            {thread_data.assistant}
            """
        )
        
        # 3. Создаем тред с начальным контекстом
        openai_thread_id, _ = await self.openai_service.create_thread_with_initial_message(
            user_name=thread_data.recipient_name,
            thread_description=f"""Это начало email переписки с {thread_data.recipient_name}.
            
            Напиши первое приветственное письмо, учитывая следующий контекст:
            {thread_data.assistant}
            
            Письмо должно:
            1. Начинаться с приветствия
            2. Представить себя как описано в контексте
            3. Объяснить цель переписки
            4. Закончиться вежливой подписью
            """
        )
        
        # 4. Запускаем ассистента для генерации ответа
        run_id = await self.openai_service.run_assistant(
            thread_id=openai_thread_id,
            assistant_id=assistant_id
        )
        
        # 5. Получаем сгенерированный ответ
        initial_message = await self.openai_service.get_response(
            thread_id=openai_thread_id,
            run_id=run_id
        )
        
        if not initial_message:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate initial message"
            )
        
        # 6. Отправляем email через Gmail API
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
            name=thread_data.name,
            description=thread_data.assistant_description
        )
        await self.assistant_repo.create_assistant_profile(assistant_profile)
        
        # 8. Создаем email тред в базе
        new_thread = EmailThread(
            id=openai_thread_id,
            user_id=thread_data.user_id,
            thread_name=thread_data.email,
            description=thread_data.assistant_description,
            status=ThreadStatus.ACTIVE,
            assistant_id=assistant_id
        )
        thread = await self.thread_repo.create_thread(new_thread)
        
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
