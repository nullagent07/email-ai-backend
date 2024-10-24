from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
import enum
from .user import Base

class MessageDirection(enum.Enum):
    INCOMING = "incoming"
    OUTGOING = "outgoing"

class MessageHistory(Base):
    __tablename__ = 'message_history'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    contact_id = Column(Integer, ForeignKey('contacts.id'), nullable=False)
    message_direction = Column(Enum(MessageDirection), nullable=False)
    message_text = Column(String, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

