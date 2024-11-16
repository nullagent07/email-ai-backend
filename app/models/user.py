from sqlalchemy import Column, String, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=True)
    is_subscription_active = Column(Boolean, default=False)
    
    # Один пользователь может иметь много oauth_credentials
    oauth_credentials = relationship(
        "OAuthCredentials", 
        back_populates="user",
        uselist=True
    )

    # Один пользователь может иметь много gmail_threads
    gmail_threads = relationship("GmailThread", back_populates="user")
    
    # Один пользователь может иметь много ассистентов
    assistants = relationship("AssistantProfile", back_populates="user")