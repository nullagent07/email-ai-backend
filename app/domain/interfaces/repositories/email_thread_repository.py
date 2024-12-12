from abc import ABC, abstractmethod
from typing import List
from uuid import UUID

from app.domain.models.email_threads import EmailThreads
from app.presentation.schemas.email_thread import EmailThreadCreate


class IEmailThreadRepository(ABC):
    """Interface for EmailThreadRepository."""

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
