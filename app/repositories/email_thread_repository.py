# app/repositories/email_thread_repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional
from app.models.email_thread import EmailThread, ThreadStatus
from sqlalchemy import and_, or_, exists
from app.models.user import User

class EmailThreadRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_thread_by_id(self, thread_id: int) -> Optional[EmailThread]:
        result = await self.db.execute(
            select(EmailThread).filter(EmailThread.id == thread_id)
        )
        return result.scalars().first()

    async def get_threads_by_user_id(self, user_id: int) -> List[EmailThread]:
        result = await self.db.execute(
            select(EmailThread).filter(EmailThread.user_id == user_id)
        )
        return result.scalars().all()
    
    async def has_active_thread_with_recipient_email(self, user_id: int, recipient_email: str) -> bool:
        result = await self.db.execute(
            select(EmailThread).filter(
                and_(
                    EmailThread.user_id == user_id,
                    EmailThread.recipient_email == recipient_email,
                    EmailThread.status == ThreadStatus.ACTIVE
                )
            )
        )
        return result.scalars().first() is not None

    async def create_thread(self, email_thread: EmailThread) -> EmailThread:
        self.db.add(email_thread)
        await self.db.commit()
        await self.db.refresh(email_thread)
        return email_thread

    async def update_thread(self, email_thread: EmailThread) -> EmailThread:
        await self.db.merge(email_thread)
        await self.db.commit()
        return email_thread

    async def delete_thread(self, email_thread: EmailThread):
        await self.db.delete(email_thread)
        await self.db.commit()

    async def get_threads_by_status(self, user_id: int, status: ThreadStatus) -> List[EmailThread]:
        result = await self.db.execute(
            select(EmailThread).filter(
                EmailThread.user_id == user_id,
                EmailThread.status == status
            )
        )
        return result.scalars().all()

    async def find_active_thread(
        self,
        sender_email: str,
        recipient_email: str
    ) -> Optional[EmailThread]:
        """
        Поиск активного треда по email отправителя и получателя
        """
        query = select(EmailThread).where(
            and_(
                EmailThread.status == ThreadStatus.ACTIVE,
                or_(
                    and_(
                        EmailThread.recipient_email == recipient_email,
                        # Проверяем, что отправитель совпадает с владельцем треда
                        exists().where(
                            and_(
                                User.id == EmailThread.user_id,
                                User.email == sender_email
                            )
                        )
                    ),
                    and_(
                        EmailThread.recipient_email == sender_email,
                        # Проверяем, что получатель совпадает с владельцем треда
                        exists().where(
                            and_(
                                User.id == EmailThread.user_id,
                                User.email == recipient_email
                            )
                        )
                    )
                )
            )
        )
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
