# app/models/__init__.py
from .user import User
from .oauth_credentials import OAuthCredentials
from .email_thread import EmailThread
from .assistant_profile import AssistantProfile

__all__ = [
    "User",
    "OAuthCredentials",
    "EmailThread",
    "EmailMessage",
    "AssistantProfile"
]
