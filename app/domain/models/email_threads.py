import uuid
from typing import Optional

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.models.assistant_profiles import AssistantProfiles
from app.domain.models.base import Base
from app.domain.models.users import Users


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

    # Отношения
    user: Mapped[Users] = relationship(back_populates="threads")
    assistant: Mapped[AssistantProfiles] = relationship(back_populates="threads")
