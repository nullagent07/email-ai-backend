from typing import Dict, Any, Optional, List
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build, Resource

from app.domain.interfaces.integrations.gmail.client import IGmailClient
from app.infrastructure.integrations.gmail.dtos.gmail_watch_dto import WatchRequestBody, WatchResponse
from core.settings import get_app_settings

import time

settings = get_app_settings()

class GmailClient(IGmailClient):
    """Implementation of Gmail API client operations."""

    def __init__(self, access_token: str, refresh_token: Optional[str] = None):
        """
        Initialize Gmail client with access token.
        
        Args:
            access_token: The OAuth 2.0 access token
        """
        self._service = self._build_service(access_token, refresh_token)

    def __del__(self):
        """Cleanup resources by closing the service."""
        if hasattr(self, '_service'):
            self._service.close()

    def _build_service(self, access_token: str, refresh_token: str = None) -> Resource:
        """
           Build Gmail API service with either simple or full OAuth2 credentials.
           
           Args:
               access_token: The access token for Gmail API
               refresh_token: Optional refresh token. If provided, will create full OAuth2 credentials
           
           Returns:
               Resource: Gmail API service resource
           """
        if refresh_token:
            creds = Credentials.from_authorized_user_info({
               "token": access_token,
               "refresh_token": refresh_token,
               "client_id": settings.google_client_id,
               "client_secret": settings.google_client_secret,
               })
        else:
            creds = Credentials(token=access_token)
           
        return build('gmail', 'v1', credentials=creds)

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
            'labelIds': ['INBOX']
        }

        response = self._service.users().watch(userId='me', body=request_body).execute()
        return response

    async def get_history(self, history_id: str) -> dict:
        """
        Gets history records after the specified history ID.
        
        Args:
            history_id: ID of the last history record that you have

        Returns:
            Dict containing history records from Gmail API
        """
        time.sleep(1)

        # Ensure history_id is a string
        history_id = str(history_id)
        
        response = self._service.users().history().list(
            userId='me',
            startHistoryId=history_id,
            historyTypes=['messageAdded'],
            maxResults=10,  # Get up to 10 history records
            labelId='INBOX'  # Only get changes in INBOX
        ).execute()
        
        print(f"Full Gmail API Response: {str(response)}")
        return response