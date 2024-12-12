from typing import Optional
from uuid import UUID

from app.domain.interfaces.orchestrators.email_thread_orchestrator import IEmailThreadOrchestrator
from app.domain.interfaces.services.email_thread_service import IEmailThreadService
from app.domain.interfaces.services.user_service import IUserService
from app.domain.interfaces.services.openai.thread_service import IOpenAIThreadService
from app.domain.models.email_threads import EmailThreads
from app.presentation.schemas.email_thread import EmailThreadCreate
from app.applications.factories.openai_factory import OpenAIFactory


class EmailThreadOrchestrator(IEmailThreadOrchestrator):
    """Orchestrator for email threads with OpenAI integration."""

    def __init__(
        self,
        email_thread_service: IEmailThreadService,
        user_service: IUserService,
    ) -> None:
        self._email_thread_service = email_thread_service
        self._user_service = user_service
        self._openai_thread_service: Optional[IOpenAIThreadService] = None

    async def initialize(
        self,
        api_key: str,
        organization: Optional[str] = None,
        api_base: Optional[str] = None,
        timeout: Optional[float] = None
    ) -> None:
        """Initialize OpenAI services."""
        _, self._openai_thread_service = await OpenAIFactory.create_services(
            api_key=api_key,
            organization=organization,
            api_base=api_base,
            timeout=timeout
        )

    async def create_thread_with_openai(
        self, user_id: UUID, assistant_id: str, thread_data: EmailThreadCreate
    ) -> EmailThreads:
        """Create a thread in OpenAI and save it to database."""
        if not self._openai_thread_service:
            raise RuntimeError("OpenAI services not initialized. Call initialize() first.")

        # Get user data
        user = await self._user_service.find_user_by_id(user_id)
        if not user:
            raise ValueError(f"User with id {user_id} not found")

        # Create thread in OpenAI
        openai_thread = await self._openai_thread_service.create_thread()
        
        # Save thread to database with OpenAI thread ID
        return await self._email_thread_service.create_thread(
            thread_id=openai_thread['id'],  # Используем ID треда из OpenAI как строку
            user_id=user_id,
            user_email=user.email,
            assistant_id=assistant_id,
            thread_data=thread_data,            
        )
