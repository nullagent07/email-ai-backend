from typing import List, Optional
from uuid import UUID

from app.domain.interfaces.repositories.email_thread_repository import IEmailThreadRepository
from app.domain.interfaces.services.email_thread_service import IEmailThreadService
from app.domain.models.email_threads import EmailThreads
from app.presentation.schemas.email_thread import EmailThreadCreate
from app.infrastructure.repositories.email_thread_repository import EmailThreadRepository
from sqlalchemy.ext.asyncio import AsyncSession


class EmailThreadService(IEmailThreadService):
    """Service for email threads."""
    
    def __init__(self, db_session: AsyncSession):
        self._repository : IEmailThreadRepository = EmailThreadRepository(
            db_session=db_session
            )
    
    async def get_threads_by_user_and_assistant(
        self, user_id: UUID, assistant_id: str
    ) -> List[EmailThreads]:
        """Get all threads for a user and assistant."""
        return await self._repository.get_threads_by_user_and_assistant(user_id, assistant_id)

    async def create_thread(
        self,
        user_id: UUID,
        user_email: str,
        assistant_id: str,
        thread_data: EmailThreadCreate,
        thread_id: str,
    ) -> EmailThreads:
        """Create a new email thread."""
        return await self._repository.create_thread(
            user_id=user_id,
            user_email=user_email,
            assistant_id=assistant_id,
            thread_data=thread_data,
            thread_id=thread_id,
        )

    async def get_active_thread_by_email(self, recipient_email: str) -> Optional[EmailThreads]:
        """
        Get active thread by recipient email.
        
        Args:
            recipient_email: Email to search for
            
        Returns:
            Active thread if found, None otherwise
        """
        return await self._repository.get_active_thread_by_email(recipient_email)

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
        return await self._repository.get_active_thread_by_email_and_user(recipient_email, user_id)
