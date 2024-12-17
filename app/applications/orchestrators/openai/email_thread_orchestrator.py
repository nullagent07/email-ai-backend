from typing import Optional
from uuid import UUID
from datetime import datetime, timedelta

from app.applications.factories.openai_factory import OpenAIFactory
from app.applications.services.gmail_api.gmail_service import GmailService
from app.applications.services.oauth_service import OAuthService
from app.applications.services.gmail_account_service import GmailAccountService
from app.domain.interfaces.services.email_thread_service import IEmailThreadService
from app.domain.interfaces.services.user_service import IUserService
from app.domain.interfaces.services.gmail_account_service import IGmailAccountService
from app.domain.interfaces.services.oauth_service import IOAuthService
from app.domain.interfaces.services.openai.thread_service import IOpenAIThreadService
from app.domain.interfaces.orchestrators.email_thread_orchestrator import IEmailThreadOrchestrator
from app.domain.models.email_threads import EmailThreads
from app.presentation.schemas.email_thread import EmailThreadCreate


class EmailThreadOrchestrator(IEmailThreadOrchestrator):
    """Orchestrator for email threads with OpenAI integration."""

    def __init__(
        self,
        email_thread_service: IEmailThreadService,
        user_service: IUserService,
        gmail_account_service: IGmailAccountService,
        oauth_service: IOAuthService,
    ) -> None:
        self._email_thread_service = email_thread_service
        self._user_service = user_service
        self._gmail_account_service = gmail_account_service
        self._oauth_service = oauth_service
        self._openai_thread_service: Optional[IOpenAIThreadService] = None
        self._topic_name: Optional[str] = None

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
        _, self._openai_thread_service = await OpenAIFactory.create_services(
            api_key=api_key,
            organization=organization,
            api_base=api_base
        )
        self._topic_name = topic_name

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
        instructions: Optional[str] = None
    ) -> Optional[str]:
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

        # Get user credentials first
        user_credentials = await self._oauth_service.find_by_access_token(access_token)
        if not user_credentials:
            raise RuntimeError("OAuth credentials not found")

        # Get Gmail account for the user
        gmail_account = await self._gmail_account_service.get_by_user_id(user_id)
        
        # If no Gmail account exists or it's expired, create/update watch
        if not gmail_account or (
            gmail_account.watch_expiration and 
            gmail_account.watch_expiration <= datetime.now()
        ):
            # Create watch using Gmail service
            watch_response = await gmail_service.create_watch(topic_name=self._topic_name)
            
            if not gmail_account:
                # Create new Gmail account with watch data
                await self._gmail_account_service.create_account(
                    oauth_credentials_id=user_credentials.id,
                    user_id=user_id,
                    history_id=watch_response.history_id,
                    expiration=datetime.fromtimestamp(int(watch_response.expiration) / 1000),  # Convert milliseconds to datetime
                    topic_name=self._topic_name
                )
            else:
                # Update existing account with new watch data
                await self._gmail_account_service.setup_watch(
                    account_id=gmail_account.id,
                    history_id=watch_response.history_id,
                    expiration=datetime.fromtimestamp(int(watch_response.expiration) / 1000),
                    topic_name=self._topic_name
                )                

        # Run the thread
        run_result = await self._openai_thread_service.run_thread(
            thread_id=thread_id,
            assistant_id=assistant_id,
            instructions=instructions
        )
        
        # Wait for the run to complete
        await self._openai_thread_service.wait_for_run_completion(thread_id, run_result["id"])
        
        # Get messages after run completion
        messages = await self._openai_thread_service.get_messages(thread_id)
        if not messages:
            return None
            
        # Get the last message which is the assistant's response
        assistant_message = messages[0]  # Messages are returned in reverse chronological order

        # Extract text content from the message
        if not assistant_message.get("content"):
            return None
            
        message_content = assistant_message["content"][0]
        if message_content["type"] != "text":
            return None

        print(message_content["text"]["value"])
            
        return message_content["text"]["value"]
