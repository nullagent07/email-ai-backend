from typing import Dict, Any, Optional, List, Tuple
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

    async def get_history(self, history_id: str, user_email: str) -> Tuple[str, str]:
        """
        Gets history records after the specified history ID.
        
        Args:
            history_id: ID of the last history record that you have
            user_email: Email of the current user

        Returns:
            Tuple containing (thread_history, receiver_email)
        """
        response = self._service.users().history().list(
            userId='me',
            startHistoryId=history_id,
            historyTypes=['messageAdded'],
            maxResults=10,
            labelId='INBOX'
        ).execute()
        
        thread_history = ""
        receiver_email = None
        
        # Check if response is not None and has 'history' key
        if response and isinstance(response, dict) and 'history' in response:
            for history_item in response['history']:
                if 'messagesAdded' in history_item:
                    for message_added in history_item['messagesAdded']:
                        message = message_added.get('message', {})
                        print("Message data:", message)  # Временно добавим для отладки
                        thread_id = message.get('threadId')
                        
                        if not thread_id:
                            continue
                        
                        # Get complete thread with all messages
                        thread = self._service.users().threads().get(
                            userId='me',
                            id=thread_id,
                            format='full'
                        ).execute()
                        
                        # Find the other participant's email
                        for msg in thread.get('messages', []):
                            headers = msg.get('payload', {}).get('headers', [])
                            from_header = next((h['value'] for h in headers if h['name'].lower() == 'from'), None)
                            if from_header and '<' in from_header:
                                email = from_header.split('<')[1].split('>')[0]
                                if email != user_email:
                                    receiver_email = email
                                    print(f"Found receiver email: {receiver_email}")
                                    break
                        
                        # Format thread history
                        messages = thread.get('messages', [])[-5:] if len(thread.get('messages', [])) > 5 else thread.get('messages', [])
                        
                        for msg in messages:
                            payload = msg.get('payload', {})
                            headers = payload.get('headers', [])
                            subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
                            from_header = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown')
                            date = next((h['value'] for h in headers if h['name'].lower() == 'date'), 'Unknown')
                            
                            thread_history += f"\nFrom: {from_header}\n"
                            thread_history += f"Date: {date}\n"
                            thread_history += f"Subject: {subject}\n"
                            
                            # Get message body
                            if 'parts' in payload:
                                for part in payload['parts']:
                                    if part['mimeType'] == 'text/plain':
                                        body = part.get('body', {}).get('data', '')
                                        if body:
                                            import base64
                                            decoded_body = base64.urlsafe_b64decode(body.encode('ASCII')).decode('utf-8')
                                            thread_history += f"Body: {decoded_body}\n"
                            elif 'body' in payload:
                                body = payload['body'].get('data', '')
                                if body:
                                    import base64
                                    decoded_body = base64.urlsafe_b64decode(body.encode('ASCII')).decode('utf-8')
                                    thread_history += f"Body: {decoded_body}\n"
                            
                            thread_history += "-" * 50 + "\n"
                        
                        # We found what we need, no need to continue processing
                        return thread_history, receiver_email
        
        return thread_history, receiver_email

    async def get_user_email(self) -> str:
        """Get the email address of the authenticated user."""
        user_info = self._service.users().getProfile(userId='me').execute()
        return user_info['emailAddress']

    async def send_email(
        self,
        to_email: str,
        subject: str,
        message_text: str,
        thread_id: Optional[str] = None
    ) -> None:
        """
        Send an email using Gmail API.
        
        Args:
            to_email: Recipient's email address
            subject: Email subject
            message_text: Base64 encoded MIME message
            thread_id: Optional thread ID for replying to a thread
        """
        message = {'raw': message_text}
        if thread_id:
            message['threadId'] = thread_id

        self._service.users().messages().send(
            userId='me',
            body=message
        ).execute()