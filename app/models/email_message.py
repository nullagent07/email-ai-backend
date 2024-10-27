from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
import enum
from .user import Base

class MessageType(enum.Enum):
    INCOMING = "incoming"
    OUTGOING = "outgoing"

class EmailMessage(Base):
    __tablename__ = 'email_messages'

    id = Column(Integer, primary_key=True, index=True)
    thread_id = Column(Integer, ForeignKey('email_threads.id'), nullable=False)
    message_type = Column(Enum(MessageType), nullable=False)
    subject = Column(String, nullable=False)
    content = Column(String, nullable=False)
    sender_email = Column(String, nullable=False)
    recipient_email = Column(String, nullable=False)
    sent_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
