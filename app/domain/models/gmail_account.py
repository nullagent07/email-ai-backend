import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.models.base import Base
from app.domain.models.oauth import OAuthCredentials
from app.domain.models.users import Users


class GmailAccount(Base):
    """Gmail account model."""

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(f"{Users.__tablename__}.id", ondelete="CASCADE"),
    )
    oauth_credentials_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(f"{OAuthCredentials.__tablename__}.id", ondelete="CASCADE"),
        unique=True,
    )

    # Watch data
    watch_history_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    watch_expiration: Mapped[Optional[datetime]] = mapped_column(nullable=True)
    watch_topic_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    oauth_credentials: Mapped["OAuthCredentials"] = relationship(back_populates="gmail_account")
    user: Mapped["Users"] = relationship(back_populates="gmail_accounts")
