from abc import ABC, abstractmethod
from typing import List
from uuid import UUID

from app.domain.models.email_threads import EmailThreads


class IEmailThreadService(ABC):
    """Interface for EmailThreadService."""

    @abstractmethod
    async def get_threads_by_user_and_assistant(
        self, user_id: UUID, assistant_id: str
    ) -> List[EmailThreads]:
        """Get all threads for a user and assistant."""
        pass
