from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from .user import Base


class GmailThread(Base):
    __tablename__ = 'gmail_threads'

    id = Column(String, primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    email_thread_id = Column(String, ForeignKey('email_threads.id'), nullable=False)
    
    recipient_email = Column(String, nullable=False)
    sender_email = Column(String, nullable=True)
    
    # Связь с пользователем
    user = relationship("User", back_populates="gmail_threads")

    # Каждый gmail_thread принадлежит одному email_thread
    email_thread = relationship("EmailThread", back_populates="gmail_thread")