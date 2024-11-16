# app/services/email_service.py

# repositories
from app.repositories.email_thread_repository import EmailThreadRepository

# models
from app.models.email_thread import EmailThread, ThreadStatus

from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import base64
from fastapi import Depends
from app.core.dependency import get_db
from uuid import UUID

class EmailThreadService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.thread_repo = EmailThreadRepository(db)

    @classmethod
    def get_instance(cls, db: AsyncSession = Depends(get_db)) -> 'EmailThreadService':
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

    