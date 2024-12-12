import uuid
from typing import List, TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.domain.models.base import Base
from app.domain.models.users import Users

if TYPE_CHECKING:
    from app.domain.models.email_threads import EmailThreads


class AssistantProfiles(Base):
    """Модель профиля ассистента."""

    id: Mapped[str] = mapped_column(String(255), primary_key=True)
    creator_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255))
    instruction: Mapped[str] = mapped_column(Text)
    capabilities: Mapped[List[str]] = mapped_column(ARRAY(String(255)))

    # Отношения
    creator: Mapped[Users] = relationship(back_populates="assistants")
    threads: Mapped[list["EmailThreads"]] = relationship(back_populates="assistant")
