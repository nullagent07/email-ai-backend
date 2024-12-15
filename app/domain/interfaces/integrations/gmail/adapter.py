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