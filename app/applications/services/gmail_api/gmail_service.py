from typing import Optional, List

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

    async def get_history_changes(self, history_id: str) -> dict:
        """
        Gets history records after the specified history ID.
        
        Args:
            history_id: ID of the last history record that you have

        Returns:
            Dict containing history records from Gmail API
        """
        if not self._adapter:
            raise RuntimeError("Gmail service not initialized")
        return await self._adapter.get_history_changes(history_id)