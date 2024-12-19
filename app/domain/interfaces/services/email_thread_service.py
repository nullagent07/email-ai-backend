from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from app.domain.models.email_threads import EmailThreads
from app.presentation.schemas.email_thread import EmailThreadCreate


class IEmailThreadService(ABC):
    """Interface for EmailThreadService."""

    @abstractmethod
    async def get_threads_by_user_and_assistant(
        self, user_id: UUID, assistant_id: str
    ) -> List[EmailThreads]:
        """Get all threads for a user and assistant."""
        pass

    @abstractmethod
    async def create_thread(
        self,
        user_id: UUID,
        user_email: str,
        assistant_id: str,
        thread_data: EmailThreadCreate,
        thread_id: str,  
    ) -> EmailThreads:
        """Create a new email thread."""
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def get_active_thread_by_email(self, recipient_email: str) -> Optional[EmailThreads]:
        """
        Get active thread by recipient email.
        
        Args:
            recipient_email: Email to search for
            
        Returns:
            Active thread if found, None otherwise
        """
        pass
