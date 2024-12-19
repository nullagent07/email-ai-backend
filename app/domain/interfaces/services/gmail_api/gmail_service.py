from typing import Optional, Protocol, List

from app.infrastructure.integrations.gmail.dtos.gmail_watch_dto import GmailWatchDTO


class IGmailService(Protocol):
    """Interface for Gmail service operations."""
    
    async def initialize(self, access_token: str, refresh_token: Optional[str] = None) -> None:
        """
        Initialize the Gmail service with access token.
        
        Args:
            access_token: The OAuth 2.0 access token for authentication
        """
        ...
        
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
        ...

    async def get_history_changes(self, history_id: str) -> dict:
        """
        Gets history records after the specified history ID.
        
        Args:
            history_id: ID of the last history record that you have

        Returns:
            Dict containing history records from Gmail API
        """
        ...
