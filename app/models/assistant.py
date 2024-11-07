from sqlalchemy import Column, String, DateTime, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from .user import Base

class AssistantProfile(Base):
    __tablename__ = 'assistant_profiles'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    thread_id = Column(UUID(as_uuid=True), ForeignKey('email_threads.id'))
    created_at = Column(DateTime(timezone=True), server_default=func.now()) 