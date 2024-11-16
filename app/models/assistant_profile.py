from sqlalchemy import Column, String, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from .user import Base

class AssistantProfile(Base):
    __tablename__ = 'assistant_profiles'
    
    id = Column(String, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    description = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Один ассистент может иметь много тредов
    threads = relationship("EmailThread", back_populates="assistant")
    
    # Связь с пользователем
    user = relationship("User", back_populates="assistants")