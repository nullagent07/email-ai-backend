from typing import Optional, List

from app.domain.interfaces.integrations.gmail.adapter import IGmailAdapter
from app.domain.interfaces.services.gmail_api.gmail_service import IGmailService
from app.infrastructure.integrations.gmail.dtos.gmail_watch_dto import GmailWatchDTO


class GmailService(IGmailService):
    """Service for managing Gmail operations."""

    def __init__(self, adapter: IGmailAdapter) -> None:
        """
        Initialize Gmail service with adapter.
        
        Args:
            adapter: Gmail adapter instance
        """
        self._adapter = adapter
        
    async def initialize(self, access_token: str) -> None:
        """
        Initialize the Gmail service with access token.
        
        Args:
            access_token: The OAuth 2.0 access token for authentication
        """
        self._adapter = IGmailAdapter(access_token)
        
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