# app/repositories/email_thread_repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from app.models.gmail_thread import GmailThread
from sqlalchemy import and_, or_, exists
from app.models.user import User

class GmailThreadRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_thread_by_id(self, thread_id: str) -> Optional[GmailThread]:
        query = select(GmailThread).where(GmailThread.id == thread_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()