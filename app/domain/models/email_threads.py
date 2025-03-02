import uuid
from typing import Optional
from enum import Enum

from sqlalchemy import ForeignKey, String, Enum as SQLAlchemyEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.models.assistant_profiles import AssistantProfiles
from app.domain.models.base import Base
from app.domain.models.users import Users


class EmailThreadStatus(str, Enum):
    """Статус email треда."""
    active = "active"
    stopped = "stopped"


class EmailThreads(Base):
    """Модель email треда."""

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    user_email: Mapped[str] = mapped_column(String(255))
    recipient_email: Mapped[str] = mapped_column(String(255))
    recipient_name: Mapped[Optional[str]] = mapped_column(String(255))
    assistant_profile_id: Mapped[str] = mapped_column(
        ForeignKey("assistant_profiles.id", ondelete="CASCADE")
    )
    instructions: Mapped[str] = mapped_column(String(1000))
    status: Mapped[EmailThreadStatus] = mapped_column(
        SQLAlchemyEnum(EmailThreadStatus),
        default=EmailThreadStatus.stopped,
        server_default=EmailThreadStatus.stopped.value,  
        nullable=False
    )

    # Отношения
    user: Mapped[Users] = relationship(back_populates="threads")
    assistant: Mapped[AssistantProfiles] = relationship(back_populates="threads")
