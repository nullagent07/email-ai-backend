from typing import Optional
from uuid import UUID
from datetime import datetime, timedelta

from app.domain.interfaces.orchestrators.email_thread_orchestrator import IEmailThreadOrchestrator
from app.domain.interfaces.services.email_thread_service import IEmailThreadService
from app.domain.interfaces.services.user_service import IUserService
from app.domain.interfaces.services.gmail_account_service import IGmailAccountService
from app.domain.interfaces.integrations.gmail.adapter import IGmailAdapter
from app.domain.interfaces.services.openai.thread_service import IOpenAIThreadService
from app.domain.models.email_threads import EmailThreads
from app.presentation.schemas.email_thread import EmailThreadCreate
from app.applications.factories.openai_factory import OpenAIFactory
from app.applications.services.gmail_api.gmail_service import GmailService


class EmailThreadOrchestrator(IEmailThreadOrchestrator):
    """Orchestrator for email threads with OpenAI integration."""

    def __init__(
        self,
        email_thread_service: IEmailThreadService,
        user_service: IUserService,
        gmail_account_service: IGmailAccountService,
    ) -> None:
        self._email_thread_service = email_thread_service
        self._user_service = user_service
        self._gmail_account_service = gmail_account_service
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
        
        # Run assistant on the thread with instructions
        await self._openai_thread_service.run_thread(
            thread_id=openai_thread['id'],
            assistant_id=assistant_id,
            instructions=thread_data.instructions
        )
        
        # Save thread to database with OpenAI thread ID
        return await self._email_thread_service.create_thread(
            thread_id=openai_thread['id'],  # Используем ID треда из OpenAI как строку
            user_id=user_id,
            user_email=user.email,
            assistant_id=assistant_id,
            thread_data=thread_data,            
        )

    async def run_thread_with_gmail_watch(
        self,
        user_id: UUID,
        access_token : str,
        thread_id: str,
        assistant_id: str,
        topic_name: str,
        instructions: Optional[str] = None
    ) -> None:
        """
        Run existing thread with Gmail watch verification.
        Creates or updates Gmail watch if needed, then runs the thread.
        
        Args:
            user_id: User's UUID
            thread_id: OpenAI thread ID to run
            assistant_id: ID of the assistant to run
            topic_name: The Cloud Pub/Sub topic where notifications will be published
            instructions: Optional instructions for the assistant
        """
        if not self._openai_thread_service:
            raise RuntimeError("OpenAI services not initialized. Call initialize() first.")

        # Initialize Gmail service
        gmail_service = GmailService()
        await gmail_service.initialize(access_token=access_token)

        # Get Gmail account for the user
        gmail_account = await self._gmail_account_service.get_by_user_id(user_id)
        
        # If no Gmail account exists, create one with watch
        if not gmail_account:
            # Create watch using Gmail service
            watch_response = await gmail_service.create_watch(topic_name=topic_name)
            
            # Create Gmail account with watch data
            await self._gmail_account_service.create_account(
                oauth_credentials_id=user_id,
                history_id=watch_response.history_id,
                expiration=datetime.fromtimestamp(int(watch_response.expiration) / 1000),  # Convert milliseconds to datetime
                topic_name=topic_name
            )
        else:
            # Check if watch token needs refresh (10 minutes threshold)
            if gmail_account.watch_expiry:
                current_time = datetime.utcnow()
                expiry_time = gmail_account.watch_expiry
                time_until_expiry = expiry_time - current_time

                # If less than 10 minutes until expiry, refresh the watch
                if time_until_expiry <= timedelta(minutes=10):
                    # Create new watch using Gmail service
                    watch_response = await gmail_service.create_watch(topic_name=topic_name)
                    
                    # Update account with new watch data
                    await self._gmail_account_service.setup_watch(
                        account_id=gmail_account.id,
                        history_id=watch_response.history_id,
                        expiration=datetime.fromtimestamp(int(watch_response.expiration) / 1000),
                        topic_name=topic_name
                    )
        
        # Run the thread
        await self._openai_thread_service.run_thread(
            thread_id=thread_id,
            assistant_id=assistant_id,
            instructions=instructions
        )
