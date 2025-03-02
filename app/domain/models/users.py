import uuid
from typing import Optional, TYPE_CHECKING, List

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.models.base import Base

if TYPE_CHECKING:
    from app.domain.models.assistant_profiles import AssistantProfiles
    from app.domain.models.email_threads import EmailThreads
    from app.domain.models.oauth import OAuthCredentials
    from app.domain.models.gmail_account import GmailAccount


class Users(Base):
    """Модель пользователя."""

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), unique=True)

    # Отношения
    assistants: Mapped[List["AssistantProfiles"]] = relationship(back_populates="creator")
    threads: Mapped[List["EmailThreads"]] = relationship(back_populates="user")
    oauth_credentials: Mapped[List["OAuthCredentials"]] = relationship(back_populates="user")
    gmail_accounts: Mapped[List["GmailAccount"]] = relationship(back_populates="user")
