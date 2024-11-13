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

    async def create_message(self, message: EmailMessage) -> EmailMessage:
        """Создает новое сообщение в базе данных"""
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        return message
