import uuid
from typing import Optional

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.models.assistant import AssistantProfile
from app.domain.models.base import Base
from app.domain.models.user import User


class EmailThread(Base):
    """Модель email треда."""

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"))
    user_email: Mapped[str] = mapped_column(String(255))
    recipient_email: Mapped[str] = mapped_column(String(255))
    recipient_name: Mapped[Optional[str]] = mapped_column(String(255))
    assistant_profile_id: Mapped[str] = mapped_column(
        ForeignKey("assistantprofile.id", ondelete="CASCADE")
    )

    # Отношения
    user: Mapped[User] = relationship(back_populates="threads")
    assistant: Mapped[AssistantProfile] = relationship(back_populates="threads")
