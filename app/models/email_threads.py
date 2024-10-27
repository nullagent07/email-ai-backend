from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Boolean
from sqlalchemy.sql import func
import enum
from .user import Base

class ThreadStatus(enum.Enum):
    ACTIVE = "active"
    CLOSED = "closed"

class EmailThread(Base):
    __tablename__ = 'email_threads'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    thread_name = Column(String, nullable=False)
    creation_date = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    description = Column(String)
    status = Column(Enum(ThreadStatus), default=ThreadStatus.ACTIVE, nullable=False)
