from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from sqlalchemy.dialects.postgresql import UUID
from .user import Base

class ThreadStatus(enum.Enum):
    ACTIVE = "active"
    CLOSED = "closed"

class EmailThread(Base):
    __tablename__ = 'email_threads'

    id = Column(String, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    thread_name = Column(String, nullable=False)
    creation_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    description = Column(String)
    status = Column(Enum(ThreadStatus), default=ThreadStatus.ACTIVE, nullable=False)
    assistant_id = Column(String, ForeignKey('assistant_profiles.id'))
    
    # Каждый тред принадлежит одному ассистенту
    assistant = relationship("AssistantProfile", back_populates="threads")
