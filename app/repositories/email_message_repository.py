# app/repositories/email_message_repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from app.models.email_message import EmailMessage, MessageType

class EmailMessageRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_message_by_id(self, message_id: int) -> Optional[EmailMessage]:
        result = await self.db.execute(
            select(EmailMessage).filter(EmailMessage.id == message_id)
        )
        return result.scalars().first()

    async def get_messages_by_thread_id(self, thread_id: int) -> List[EmailMessage]:
        result = await self.db.execute(
            select(EmailMessage).filter(EmailMessage.thread_id == thread_id)
        )
        return result.scalars().all()

    async def get_messages_by_sender_email(self, sender_email: str) -> List[EmailMessage]:
        result = await self.db.execute(
            select(EmailMessage).filter(EmailMessage.sender_email == sender_email)
        )
        return result.scalars().all()

    async def create_message(self, email_message: EmailMessage) -> EmailMessage:
        self.db.add(email_message)
        await self.db.commit()
        await self.db.refresh(email_message)
        return email_message

    async def update_message(self, email_message: EmailMessage) -> EmailMessage:
        await self.db.merge(email_message)
        await self.db.commit()
        return email_message

    async def delete_message(self, email_message: EmailMessage):
        await self.db.delete(email_message)
        await self.db.commit()
