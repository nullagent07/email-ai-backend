from typing import List, Optional
from uuid import UUID

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.models.email_threads import EmailThreads, EmailThreadStatus
from app.domain.interfaces.repositories.email_thread_repository import IEmailThreadRepository
from app.presentation.schemas.email_thread import EmailThreadCreate


class EmailThreadRepository(IEmailThreadRepository):
    """Repository for email threads."""

    def __init__(self, db_session: AsyncSession) -> None:
        self.db_session = db_session

    async def get_threads_by_user_and_assistant(
        self, user_id: UUID, assistant_id: str
    ) -> List[EmailThreads]:
        """Get all threads for a user and assistant."""
        query = select(EmailThreads).where(
            EmailThreads.user_id == user_id,
            EmailThreads.assistant_profile_id == assistant_id
        )
        result = await self.db_session.execute(query)
        return list(result.scalars().all())

    async def create_thread(
        self,
        user_id: UUID,
        user_email: str,
        assistant_id: str,
        thread_data: EmailThreadCreate,
        thread_id: str,  
    ) -> EmailThreads:
        """Create a new email thread."""
        if thread_data.status is None:
            thread_data.status = EmailThreadStatus.stopped
        thread = EmailThreads(
            id=thread_id,  
            user_id=user_id,
            user_email=user_email,
            recipient_email=thread_data.recipient_email,
            recipient_name=thread_data.recipient_name,
            assistant_profile_id=assistant_id,
            instructions=thread_data.instructions,
            status=thread_data.status,
        )
        self.db_session.add(thread)
        await self.db_session.commit()
        await self.db_session.refresh(thread)
        return thread

    async def get_active_thread_by_email(self, recipient_email: str) -> Optional[EmailThreads]:
        """
        Get active thread by recipient email.
        
        Args:
            recipient_email: Email to search for
            
        Returns:
            Active thread if found, None otherwise
        """
        query = select(EmailThreads).where(
            and_(
                EmailThreads.recipient_email == recipient_email,
                EmailThreads.status == EmailThreadStatus.active
            )
        )
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()

    async def get_active_thread_by_email_and_user(
        self, 
        recipient_email: str,
        user_id: UUID
    ) -> Optional[EmailThreads]:
        """
        Get active thread by recipient email and user ID.
        
        Args:
            recipient_email: Email to search for
            user_id: ID of the user who owns the thread
            
        Returns:
            Active thread if found, None otherwise
        """
        query = select(EmailThreads).where(
            and_(
                EmailThreads.recipient_email == recipient_email,
                EmailThreads.user_id == user_id,
                EmailThreads.status == EmailThreadStatus.active
            )
        )
        result = await self.db_session.execute(query)
        return result.scalar_one_or_none()
