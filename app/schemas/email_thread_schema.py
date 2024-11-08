# app/schemas/email_thread_schema.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum
from uuid import UUID
from .assistant_profile_schema import AssistantProfileCreate
class ThreadStatus(str, Enum):
    ACTIVE = "active"
    CLOSED = "closed"

class EmailThreadBase(BaseModel):
    user_id: Optional[UUID] = None
    

class EmailThreadCreate(EmailThreadBase):
    recipient_email: str  # Email адрес получателя
    recipient_name: str   # Имя получателя
    assistant: str        # ID или имя ассистента
    # assistant: AssistantProfileCreate 

class EmailThreadUpdate(EmailThreadBase):
    status: ThreadStatus

class EmailThreadResponse(EmailThreadBase):
    id: str
    user_id: UUID
    creation_date: datetime
    status: ThreadStatus

    class Config:
        from_attributes = True
