# app/services/email_service.py

# repositories
from app.repositories.open_ai_thread_repository import OpenAiThreadRepository

# models
from app.models.open_ai_thread import OpenAiThread, ThreadStatus

from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import base64
from fastapi import Depends
from app.core.dependency import get_db
from uuid import UUID
from typing import Optional

class OpenAiThreadService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.open_ai_thread_repo = OpenAiThreadRepository(db)

    @classmethod
    def get_instance(cls, db: AsyncSession = Depends(get_db)) -> 'OpenAiThreadService':
        return cls(db)
    
    async def get_assistant_id_by_thread_id(self, thread_id: int) -> Optional[str]:
        return await self.open_ai_thread_repo.get_assistant_id_by_thread_id(thread_id)
    
    async def create_thread(self, 
                            id: str, 
                            user_id: UUID, 
                            description: str, 
                            assistant_id: str, 
                            recipient_email: str, 
                            sender_email: str,
                            recipient_name: Optional[str] = None,
                            sender_name: Optional[str] = None
                            ) -> OpenAiThread:
        """Создает новый email-тред в базе данных."""
        
        # Создаем новый тред
        new_thread = OpenAiThread(
            id=id, 
            user_id=user_id, 
            description=description, 
            assistant_id=assistant_id, 
            recipient_email=recipient_email, 
            recipient_name=recipient_name,
            sender_email=sender_email,
            sender_name=sender_name
        )
        
        return await self.open_ai_thread_repo.create_thread(new_thread)

    async def get_thread_id_by_user_id_and_recipient_email(self, user_id: UUID, recipient_email: str) -> Optional[int]:
        return await self.open_ai_thread_repo.get_thread_id_by_user_id_and_recipient_email(user_id, recipient_email)

    async def get_user_threads(self, user_id: int) -> List[OpenAiThread]:
        return await self.open_ai_thread_repo.get_threads_by_user_id(user_id)

    async def close_email_thread(self, thread_id: int) -> OpenAiThread:
        thread = await self.open_ai_thread_repo.get_thread_by_id(thread_id)
        if not thread:
            raise ValueError("Thread not found")
        thread.status = ThreadStatus.CLOSED
        return await self.open_ai_thread_repo.update_thread(thread)

    async def get_threads_by_status(self, user_id: int, status: ThreadStatus) -> List[OpenAiThread]:
        return await self.open_ai_thread_repo.get_threads_by_status(user_id, status)

    def compose_email_body(self, sender_email: str, recipient_email: str, content: str, thread_id: Optional[str] = None) -> dict:
        """Формирует тело email для отправки через Gmail API."""
        return {
            'raw': base64.urlsafe_b64encode(
                f"From: {sender_email}\r\nTo: {recipient_email}\r\nSubject: New conversation\r\nMIME-Version: 1.0\r\nContent-Type: text/html; charset=utf-8\r\n\r\n{content}\r\n\r\nThread ID: {thread_id}".encode()
            ).decode()
        }

    async def has_active_thread_with_recipient_email(self, user_id: UUID, recipient_email: str) -> bool:
        return await self.open_ai_thread_repo.has_active_thread_with_recipient_email(user_id, recipient_email)

    