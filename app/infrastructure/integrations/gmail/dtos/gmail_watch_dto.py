from dataclasses import dataclass
from typing import List, Optional, TypedDict


class WatchRequestBody(TypedDict):
    """
    Type for Gmail API watch request body.
    https://developers.google.com/gmail/api/reference/rest/v1/users/watch#request-body
    """
    topicName: str
    labelIds: Optional[List[str]]


class WatchResponse(TypedDict):
    """
    Type for Gmail API watch response.
    https://developers.google.com/gmail/api/reference/rest/v1/users/watch#response
    """
    historyId: str
    expiration: str  # Unix timestamp in milliseconds


@dataclass
class GmailWatchDTO:
    """Data transfer object for Gmail watch operation."""
    
    history_id: str
    expiration: str  # Unix timestamp in milliseconds
    topic_name: str
    label_filters: Optional[List[str]] = None
