from typing import Optional, List, Tuple
import base64
from email.mime.text import MIMEText

from app.domain.interfaces.integrations.gmail.adapter import IGmailAdapter
from app.infrastructure.integrations.gmail.client import GmailClient
from app.infrastructure.integrations.gmail.dtos.gmail_watch_dto import GmailWatchDTO


class GmailAdapter(IGmailAdapter):
    """Adapter for Gmail API."""

    def __init__(self, access_token: str, refresh_token: Optional[str] = None) -> None:
        """Initialize Gmail adapter."""
        self._client = GmailClient(access_token, refresh_token)

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
        watch_response = await self._client.create_watch(
            topic_name=topic_name,
            label_filters=label_filters
        )
        
        return GmailWatchDTO(
            history_id=watch_response.get('historyId'),
            expiration=watch_response.get('expiration')
        )

    async def get_history_changes(self, history_id: str, user_email: str) -> Tuple[str, str]:
        """Gets history records after the specified history ID."""
        return await self._client.get_history(history_id=history_id, user_email=user_email)

    def compose_email_body(
        self,
        sender_email: str,
        recipient_email: str,
        content: str,
        subject: str,
        thread_id: Optional[str] = None,
        references: Optional[str] = None,
        in_reply_to: Optional[str] = None
    ) -> dict:
        """
        Формирует тело email для отправки через Gmail API.
        
        Args:
            sender_email: Email отправителя
            recipient_email: Email получателя
            content: Текст сообщения
            subject: Тема письма
            thread_id: ID треда (опционально)
            references: ID писем в цепочке (опционально)
            in_reply_to: ID письма, на которое отвечаем (опционально)
            
        Returns:
            Подготовленное тело сообщения для Gmail API
        """
        message = MIMEText(content, 'html')
        message['From'] = sender_email
        message['To'] = recipient_email
        message['Subject'] = subject

        if in_reply_to:
            message['In-Reply-To'] = in_reply_to
        if references:
            message['References'] = references
            
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        body = {
            'raw': raw_message
        }
        if thread_id:
            body['threadId'] = thread_id

        return body

    async def send_email(
        self,
        to_email: str,
        subject: str,
        message_text: str,
        thread_id: Optional[str] = None,
        references: Optional[str] = None,
        in_reply_to: Optional[str] = None
    ) -> None:
        """
        Send an email using Gmail API.
        
        Args:
            to_email: Recipient's email address
            subject: Email subject
            message_text: Email body text
            thread_id: Optional thread ID for replying to a thread
            references: Optional message IDs in the email chain
            in_reply_to: Optional message ID we're replying to
        """
        # Get sender email from Gmail profile
        sender_email = await self._client.get_user_email()
        
        # Compose email body
        message = self.compose_email_body(
            sender_email=sender_email,
            recipient_email=to_email,
            content=message_text,
            subject=subject,
            thread_id=thread_id,
            references=references,
            in_reply_to=in_reply_to
        )

        await self._client.send_email(
            to_email=to_email,
            subject=subject,
            message_text=message['raw'],
            thread_id=message.get('threadId')
        )