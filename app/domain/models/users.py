import uuid
from typing import Optional

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.models.base import Base


class Users(Base):
    """Модель пользователя."""

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True)

    # Отношения
    assistants: Mapped[list["AssistantProfiles"]] = relationship(back_populates="creator")
    threads: Mapped[list["EmailThreads"]] = relationship(back_populates="user")
    oauth_credentials: Mapped[list["OAuthCredentials"]] = relationship(back_populates="user")
