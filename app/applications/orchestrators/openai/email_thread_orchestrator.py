from typing import Optional
from uuid import UUID
from datetime import datetime, timedelta
import asyncio

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
from app.domain.models.users import Users
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

        # Get user credentials first
        user_credentials = await self._oauth_service.find_by_access_token(access_token)
        if not user_credentials:
            raise RuntimeError("OAuth credentials not found")

        # Initialize Gmail service
        gmail_service = GmailService()
        await gmail_service.initialize(access_token=access_token, refresh_token=user_credentials.refresh_token)

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

    async def handle_gmail_notification(self, notification_data: dict) -> None:
        """
        Handle Gmail push notification.
        
        Args:
            notification_data: The notification data from Gmail
        """
        try:
            # print("Raw notification data:", notification_data)
            
            # PubSub sends data in base64 format
            import base64
            import json
            
            # Get the base64 encoded data
            encoded_data = notification_data.get('message', {}).get('data')
            if not encoded_data:
                raise ValueError("No data found in notification")
                
            # Decode base64 and parse JSON
            decoded_data = base64.b64decode(encoded_data).decode('utf-8')
            # print("Decoded data:", decoded_data)
            data = json.loads(decoded_data)
            print("Parsed JSON:", data)
            
            # Extract email address and history ID
            email_address = data.get('emailAddress')
            history_id = data.get('historyId')

            print(f"Extracted data - email: {email_address}, history_id: {history_id}")
            
            if not email_address:
                raise ValueError("Email address not found in notification data")
            if not history_id:
                raise ValueError("History ID not found in notification data")

            # Get the associated Gmail account by email
            user = await self._user_service.find_user_by_email(email_address)
            if not user:
                raise ValueError(f"User not found for email: {email_address}")

            gmail_account = await self._gmail_account_service.get_by_user_id(user.id)
            if not gmail_account:
                raise ValueError(f"Gmail account not found for user: {user.id}")

            # Get OAuth credentials
            oauth_creds = await self._oauth_service.find_credentials_by_email(email_address)
            if not oauth_creds:
                raise ValueError("OAuth credentials not found")

            # Initialize Gmail service
            gmail_service = GmailService()
            await gmail_service.initialize(
                access_token=oauth_creds.access_token,
                refresh_token=oauth_creds.refresh_token
            )

            # Get stored history ID or use the one from notification
            stored_history_id = gmail_account.watch_history_id
            if not stored_history_id:
                print(f"No stored history ID found, using the one from notification")
                stored_history_id = str(history_id)

            # Get changes since last history ID
            thread_history, receiver_email = await gmail_service.get_history_changes(
                history_id=stored_history_id,
                user_email=email_address
            )
            print(f"Thread history: {thread_history}")
            print(f"Receiver email: {receiver_email}")

            # Find active thread by recipient email and user ID
            active_thread = await self._email_thread_service.get_active_thread_by_email_and_user(
                recipient_email=receiver_email,
                user_id=user.id
            )
                                
            if active_thread:
                print(f"Found active thread with ID: {active_thread.id}")
                print(f"Found active assistant_profile_id: {active_thread.assistant_profile_id}")
                print(f"Found active instructions: {active_thread.instructions}")

                runs = await self._openai_thread_service.list_runs(
                    thread_id=active_thread.id
                )
                print("Successfully listed runs")
                
                # Проверяем активные runs
                active_runs = [
                    run for run in runs 
                    if run['status'] not in ['completed', 'cancelled', 'failed', 'expired']
                ]
                
                if active_runs:
                    print(f"Found {len(active_runs)} active runs, cancelling them...")
                    for run in active_runs:
                        await self._openai_thread_service.cancel_run(
                            thread_id=active_thread.id,
                            run_id=run['id']
                        )
                        print(f"Cancelled run {run['id']}")
                
                print("Deleting all messages from thread...")
                await self._openai_thread_service.delete_all_messages(active_thread.id)
                print("Successfully deleted all messages")

                print("Adding new message to thread...")
                await self._openai_thread_service.add_message(
                    thread_id=active_thread.id,
                    content=thread_history,
                    role="user"
                )
                print("Successfully added message")

                print(active_thread.id)
                print(active_thread.assistant_profile_id)
                print(active_thread.instructions)

                print("Starting new run...")
                run_result = await self._openai_thread_service.run_thread(
                    thread_id=active_thread.id,
                    assistant_id=active_thread.assistant_profile_id,
                    instructions=active_thread.instructions
                )
                print("Run result:", run_result)
                
                # Используем безопасный метод .get() для доступа к полям словаря
                run_id = run_result.get("id")
                if not run_id:
                    raise ValueError("Failed to get run ID from response")
                print(f"Got run ID: {run_id}")
                
                print(f"Waiting for run {run_id} to complete...")
                await self._openai_thread_service.wait_for_run_completion(
                    thread_id=active_thread.id,
                    run_id=run_id,
                    timeout=60.0
                )
                print(f"Run {run_id} completed successfully")
            else:
                print(f"No active thread found for email {email_address}")
                
        except Exception as e:
            print(f"Failed to process Gmail notification: {e}")
            raise
