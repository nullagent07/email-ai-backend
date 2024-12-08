import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.models.base import Base
from app.domain.models.users import Users


class OAuthCredentials(Base):
    """Модель OAuth учетных данных."""

    __table_args__ = (
        UniqueConstraint('email', 'provider', name='uq_oauth_email_provider'),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    provider: Mapped[str] = mapped_column(String(255))
    access_token: Mapped[str] = mapped_column(Text)
    refresh_token: Mapped[str] = mapped_column(Text)
    expires_at: Mapped[datetime] = mapped_column()
    email: Mapped[str] = mapped_column(String(255))
    provider_data: Mapped[dict] = mapped_column(JSON)

    # Отношения
    user: Mapped[Users] = relationship(back_populates="oauth_credentials")
