from abc import ABC, abstractmethod
from app.infrastructure.integrations.gmail.dto.gmail_watch_dto import GmailWatchDTO

class IGmailAdapter(ABC):
    """Interface for Gmail API adapter operations."""
    
    @abstractmethod
    async def create_watch(self, topic_name: str, label_filters: list[str] | None = None) -> GmailWatchDTO:
        """
        Sets up a watch on the user's inbox for email notifications.
        
        Args:
            topic_name: The Cloud Pub/Sub topic where notifications will be published
            label_filters: Optional list of Gmail labels to filter notifications
            
        Returns:
            GmailWatchDTO containing watch details including historyId and expiration
        """
        pass