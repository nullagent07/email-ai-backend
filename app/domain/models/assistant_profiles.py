import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.models.base import Base
from app.domain.models.users import Users


class AssistantProfiles(Base):
    """Модель профиля ассистента."""

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    creator_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    instruction: Mapped[str] = mapped_column(Text)

    # Отношения
    creator: Mapped[Users] = relationship(back_populates="assistants")
    threads: Mapped[list["EmailThreads"]] = relationship(back_populates="assistant")
