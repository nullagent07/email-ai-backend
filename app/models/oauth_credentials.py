from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.dialects.postgresql import JSON
import uuid
from .user import Base

class OAuthCredentials(Base):
    __tablename__ = 'oauth_credentials'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    provider = Column(String, nullable=False)  # 'google', 'facebook' etc
    access_token = Column(String, nullable=True)
    refresh_token = Column(String, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    email = Column(String, nullable=False)
    provider_data = Column(JSON, nullable=True)


    # Связь с User
    user = relationship("User", back_populates="oauth_credentials")
    
    # Добавим составной уникальный индекс
    __table_args__ = (
        UniqueConstraint('user_id', 'provider', name='uq_user_provider'),
    )
