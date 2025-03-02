from typing import Optional, Protocol

from app.infrastructure.integrations.gmail.dtos.gmail_watch_dto import GmailWatchDTO


class IGmailAdapter(Protocol):
    """Interface for Gmail API adapter operations."""
    
    async def create_watch(self, topic_name: str, label_filters: Optional[list[str]] = None) -> GmailWatchDTO:
        """
        Sets up a watch on the user's inbox.
        
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