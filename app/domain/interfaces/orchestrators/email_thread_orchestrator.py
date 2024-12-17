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
        topic_name: Optional[str] = None
    ) -> None:
        """
        Initialize the orchestrator with OpenAI credentials.
        
        Args:
            api_key: OpenAI API key
            organization: Optional organization ID
            api_base: Optional API base URL
            topic_name: Optional topic name for Gmail watch
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

    @abstractmethod
    async def run_thread_with_gmail_watch(
        self,
        user_id: UUID,
        access_token: str,
        thread_id: str,
        assistant_id: str,
        instructions: Optional[str] = None
    ) -> None:
        """
        Run existing thread with Gmail watch verification.
        Creates or updates Gmail watch if needed, then runs the thread.
        
        Args:
            user_id: User's UUID
            access_token: Gmail OAuth access token
            thread_id: OpenAI thread ID to run
            assistant_id: ID of the assistant to run
            topic_name: The Cloud Pub/Sub topic where notifications will be published
            instructions: Optional instructions for the assistant
        """
        pass
