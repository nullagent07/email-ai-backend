from typing import Dict, Any, Optional, List
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build, Resource

from app.domain.interfaces.integrations.gmail.client import IGmailClient
from app.infrastructure.integrations.gmail.dtos.gmail_watch_dto import WatchRequestBody, WatchResponse


class GmailClient(IGmailClient):
    """Implementation of Gmail API client operations."""

    def __init__(self, access_token: str):
        """
        Initialize Gmail client with access token.
        
        Args:
            access_token: The OAuth 2.0 access token
        """
        self._service = self._build_service(access_token)

    def __del__(self):
        """Cleanup resources by closing the service."""
        if hasattr(self, '_service'):
            self._service.close()

    def _build_service(self, access_token: str) -> Resource:
        """
        Creates Gmail API service with provided credentials.
        
        Args:
            access_token: The OAuth 2.0 access token
            
        Returns:
            Gmail API service resource
        """
        credentials = Credentials(token=access_token)
        return build('gmail', 'v1', credentials=credentials)

    async def watch(self, topic_name: str, label_ids: Optional[List[str]] = None) -> WatchResponse:
        """
        Creates a watch on the user's mailbox using Gmail API.
        
        Args:
            topic_name: The Cloud Pub/Sub topic to publish notifications to
            label_ids: Optional list of label IDs to restrict notifications to
            
        Returns:
            WatchResponse containing the watch response from Gmail API
        """
        request_body: WatchRequestBody = {
            'topicName': topic_name,
            'labelIds': label_ids or ['INBOX']
        }

        response = self._service.users().watch(userId='me', body=request_body).execute()
        return response