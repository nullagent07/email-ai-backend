from typing import Optional, List, Tuple

from app.domain.interfaces.integrations.gmail.adapter import IGmailAdapter
from app.domain.interfaces.services.gmail_api.gmail_service import IGmailService
from app.infrastructure.integrations.gmail.dtos.gmail_watch_dto import GmailWatchDTO
from app.infrastructure.integrations.gmail.adapter import GmailAdapter


class GmailService(IGmailService):
    """Service for managing Gmail operations."""

    def __init__(self) -> None:
        """Initialize Gmail service."""
        self._adapter = None
        
    async def initialize(self, access_token: str, refresh_token: Optional[str] = None) -> None:
        """
        Initialize the Gmail service with access token.
        
        Args:
            access_token: The OAuth 2.0 access token for authentication
        """
        self._adapter = GmailAdapter(access_token, refresh_token)
        
    async def create_watch(
        self,
        topic_name: str,
        label_filters: Optional[List[str]] = None
    ) -> GmailWatchDTO:
        """
        Create a watch on the user's inbox.
        
        Args:
            topic_name: The Cloud Pub/Sub topic where notifications will be published
            label_filters: Optional list of Gmail labels to filter notifications
            
        Returns:
            GmailWatchDTO containing watch subscription details
        """
        return await self._adapter.create_watch(
            topic_name=topic_name,
            label_filters=label_filters
        )

    async def get_history(self, history_id: str, user_email: str) -> Tuple[str, str]:
        """Gets history records after the specified history ID."""
        if not self._adapter:
            raise RuntimeError("Gmail service not initialized")
        return await self._adapter.get_history(history_id=history_id, user_email=user_email)

    async def get_history_changes(self, history_id: str, user_email: str) -> Tuple[str, str]:
        """Gets history records after the specified history ID."""
        if not self._adapter:
            raise RuntimeError("Gmail service not initialized")
        return await self._adapter.get_history_changes(history_id=history_id, user_email=user_email)

    async def send_email(
        self,
        to_email: str,
        subject: str,
        message_text: str,
        thread_id: Optional[str] = None
    ) -> None:
        """
        Send an email using Gmail API.
        
        Args:
            to_email: Recipient's email address
            subject: Email subject
            message_text: Email body text
            thread_id: Optional thread ID for replying to a thread
        """
        if not self._adapter:
            raise RuntimeError("Gmail service not initialized")
        await self._adapter.send_email(
            to_email=to_email,
            subject=subject,
            message_text=message_text,
            thread_id=thread_id
        )