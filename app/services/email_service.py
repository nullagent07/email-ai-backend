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
from app.repositories.assistant_profile_repository import AssistantProfileRepository
from app.models.assistant_profile import AssistantProfile

from app.core.config import settings
import base64
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from fastapi import HTTPException, status
from app.repositories.oauth_credentials_repository import OAuthCredentialsRepository
from fastapi import Depends
from app.core.dependency import get_db
from uuid import UUID
class EmailService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.message_repo = EmailMessageRepository(db)
        self.thread_repo = EmailThreadRepository(db)
        self.assistant_repo = AssistantProfileRepository(db)
        self.oauth_repo = OAuthCredentialsRepository(db)
        self.openai_service = OpenAIService()

    @classmethod
    def get_instance(cls, db: AsyncSession = Depends(get_db)) -> 'EmailService':
        return cls(db)
    
    async def create_thread(self, new_thread: EmailThread) -> EmailThread:
        """Создает новый email-тред в базе данных."""
        return await self.thread_repo.create_thread(new_thread)
    
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

    def compose_email_body(self, sender_email: str, recipient_email: str, content: str) -> dict:
        """Формирует тело email для отправки через Gmail API."""
        return {
            'raw': base64.urlsafe_b64encode(
                f"From: {sender_email}\r\nTo: {recipient_email}\r\nSubject: New conversation\r\nMIME-Version: 1.0\r\nContent-Type: text/html; charset=utf-8\r\n\r\n{content}".encode()
            ).decode()
        }

    async def has_active_thread_with_recipient_email(self, user_id: UUID, recipient_email: str) -> bool:
        return await self.thread_repo.has_active_thread_with_recipient_email(user_id, recipient_email)


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

    