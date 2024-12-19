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

    async def get_message(self, message_id: str) -> dict:
        """
        Get a specific message by its ID.
        
        Args:
            message_id: The ID of the message to retrieve

        Returns:
            Dict containing the message details
        """
        return self._service.users().messages().get(
            userId='me',
            id=message_id,
            format='full'
        ).execute()

    async def get_thread(self, thread_id: str) -> dict:
        """
        Get a complete thread with all messages by thread ID.
        
        Args:
            thread_id: The ID of the thread to retrieve

        Returns:
            Dict containing the complete thread with all messages
        """
        return self._service.users().threads().get(
            userId='me',
            id=thread_id,
            format='full'
        ).execute()

    async def get_history(self, history_id: str) -> dict:
        """
        Gets history records after the specified history ID.
        
        Args:
            history_id: ID of the last history record that you have

        Returns:
            Dict containing history records from Gmail API
        """
        response = self._service.users().history().list(
            userId='me',
            startHistoryId=history_id,
            historyTypes=['messageAdded'],
            maxResults=10,  # Get up to 10 history records
            labelId='INBOX'  # Only get changes in INBOX
        ).execute()
        
        # If there are messages added, get their thread history
        if 'history' in response:
            for history_item in response['history']:
                if 'messagesAdded' in history_item:
                    for message_added in history_item['messagesAdded']:
                        thread_id = message_added['message']['threadId']
                        print(f"\n=== Getting thread history for thread {thread_id} ===")
                        
                        # Get complete thread with all messages
                        thread = self._service.users().threads().get(
                            userId='me',
                            id=thread_id,
                            format='full'
                        ).execute()
                        
                        print("\n=== Last 5 Messages in Thread ===")
                        # Get last 5 messages
                        messages = thread['messages'][-5:] if len(thread['messages']) > 5 else thread['messages']
                        
                        for msg in messages:
                            headers = msg['payload']['headers']
                            subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
                            from_header = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown')
                            date = next((h['value'] for h in headers if h['name'].lower() == 'date'), 'Unknown')
                            
                            print(f"\nFrom: {from_header}")
                            print(f"Date: {date}")
                            print(f"Subject: {subject}")
                            
                            # Get message body
                            if 'parts' in msg['payload']:
                                for part in msg['payload']['parts']:
                                    if part['mimeType'] == 'text/plain':
                                        body = part.get('body', {}).get('data', '')
                                        if body:
                                            import base64
                                            decoded_body = base64.urlsafe_b64decode(body.encode('ASCII')).decode('utf-8')
                                            print(f"Body: {decoded_body}\n")
                            elif 'body' in msg['payload']:
                                body = msg['payload']['body'].get('data', '')
                                if body:
                                    import base64
                                    decoded_body = base64.urlsafe_b64decode(body.encode('ASCII')).decode('utf-8')
                                    print(f"Body: {decoded_body}\n")
                            
                            print("-" * 50)
                        
                        # Store thread in the response
                        message_added['thread'] = thread
        
        # print(f"\nFull Gmail API Response: {str(response)}")
        return response