from sqlalchemy import Column, String, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from sqlalchemy.dialects.postgresql import UUID
from .user import Base

class ThreadStatus(enum.Enum):
    ACTIVE = "active"
    CLOSED = "closed"

class OpenAiThread(Base):
    __tablename__ = 'openai_threads'

    id = Column(String, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    creation_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    description = Column(String)
    status = Column(Enum(ThreadStatus), default=ThreadStatus.ACTIVE, nullable=False)
    assistant_id = Column(String, ForeignKey('assistant_profiles.id'))
    
    # Поле получателя
    recipient_email = Column(String, nullable=False)  # Email получателя
    recipient_name = Column(String, nullable=True)   # Имя получателя
    # Поле отправителя
    sender_email = Column(String, nullable=False)
    sender_name = Column(String, nullable=True)
    
    # Каждый тред принадлежит одному ассистенту
    assistant = relationship("AssistantProfile", back_populates="threads")
