from abc import ABC, abstractmethod
from typing import Optional
from uuid import UUID

from app.domain.models.email_threads import EmailThreads
from app.presentation.schemas.email_thread import EmailThreadCreate


class IEmailThreadOrchestrator(ABC):
    """Interface for orchestrating email thread operations."""

    @abstractmethod
    async def initialize(
        self,
        api_key: str,
        organization: Optional[str] = None,
        api_base: Optional[str] = None,
        timeout: Optional[float] = None
    ) -> None:
        """
        Initialize the orchestrator with OpenAI credentials.
        
        Args:
            api_key: OpenAI API key
            organization: Optional organization ID
            api_base: Optional API base URL
            timeout: Optional request timeout
        """
        pass

    @abstractmethod
    async def create_thread_with_openai(
        self, user_id: UUID, assistant_id: str, thread_data: EmailThreadCreate
    ) -> EmailThreads:
        """
        Create a thread in OpenAI and save it to database.
        
        Args:
            user_id: ID of the user creating the thread
            assistant_id: ID of the assistant
            thread_data: Thread creation data
            
        Returns:
            Created email thread
        """
        pass
