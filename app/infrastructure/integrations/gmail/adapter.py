from datetime import datetime

from app.domain.interfaces.integrations.gmail.adapter import IGmailAdapter
from app.infrastructure.integrations.gmail.client import GmailClient
from app.infrastructure.integrations.gmail.dtos.gmail_watch_dto import GmailWatchDTO


class GmailAdapter(IGmailAdapter):
    """Implementation of Gmail API adapter operations."""

    def __init__(self, access_token: str):
        """
        Initialize Gmail adapter with access token.
        
        Args:
            access_token: The OAuth 2.0 access token for authentication
        """
        self._client = GmailClient(access_token)

    async def create_watch(self, topic_name: str, label_filters: list[str] | None = None) -> GmailWatchDTO:
        """
        Sets up a watch on the user's inbox and converts response to DTO.
        
        Args:
            topic_name: The Cloud Pub/Sub topic where notifications will be published
            label_filters: Optional list of Gmail labels to filter notifications
            
        Returns:
            GmailWatchDTO containing watch subscription details
        """
        response = await self._client.watch(
            topic_name=topic_name,
            label_ids=label_filters
        )

        return GmailWatchDTO(
            history_id=response['historyId'],
            expiration=response['expiration'],
            topic_name=topic_name,
            label_filters=label_filters
        )