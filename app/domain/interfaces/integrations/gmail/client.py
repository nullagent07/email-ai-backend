from abc import ABC, abstractmethod
from typing import Optional, List

from app.infrastructure.integrations.gmail.dtos.gmail_watch_dto import WatchResponse


class IGmailClient(ABC):
    """Interface for Gmail API client operations."""
    
    @abstractmethod
    async def watch(self, topic_name: str, label_ids: Optional[List[str]] = None) -> WatchResponse:
        """
        Creates a watch on the user's mailbox.
        
        Args:
            topic_name: The Cloud Pub/Sub topic to publish notifications to
            label_ids: Optional list of label IDs to restrict notifications to
            
        Returns:
            WatchResponse containing the watch response from Gmail API
        """
        pass

    @abstractmethod
    async def get_history(self, history_id: str) -> dict:
        """
        Gets history records after the specified history ID.
        
        Args:
            history_id: ID of the last history record that you have

        Returns:
            Dict containing history records from Gmail API
        """
        pass