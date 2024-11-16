
# app/repositories/email_thread_repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from app.models.gmail_thread import GmailThread
from sqlalchemy import and_, or_, exists
from app.models.user import User
from fastapi import Depends
from app.core.dependency import get_db
from app.repositories.gmail_thread_repository import GmailThreadRepository

class GmailThreadService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.gmail_thread_repository = GmailThreadRepository(db)

    @classmethod
    def get_instance(cls, db: AsyncSession = Depends(get_db)) -> 'GmailThreadService':
        return cls(db)

    async def create_gmail_thread(self, gmail_thread_id: str, user_id: int, open_ai_thread_id: str, recipient_email: str) -> GmailThread:
        """Создает новый GmailThread."""
        
        new_gmail_thread = GmailThread(
            id=gmail_thread_id,
            user_id=user_id,
            open_ai_thread_id=open_ai_thread_id,
            recipient_email=recipient_email
        )
        
        return await self.gmail_thread_repository.create_gmail_thread(new_gmail_thread)