from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from .user import Base

class OAuthCredentials(Base):
    __tablename__ = 'oauth_credentials'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    provider = Column(String, nullable=False) # 'google', 'facebook' etc
    access_token = Column(String, nullable=True)
    refresh_token = Column(String, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    email = Column(String, nullable=False)
    
    # Связь с User
    user = relationship("User", back_populates="oauth_credentials")

    # Добавим составной уникальный индекс
    __table_args__ = (
        UniqueConstraint('user_id', 'provider', name='uq_user_provider'),
    )
