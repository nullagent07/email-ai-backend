# app/schemas/email_thread_schema.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

class ThreadStatus(str, Enum):
    ACTIVE = "active"
    CLOSED = "closed"

class EmailThreadBase(BaseModel):
    thread_name: str
    description: Optional[str] = None

class EmailThreadCreate(EmailThreadBase):
    user_id: int

class EmailThreadUpdate(EmailThreadBase):
    status: ThreadStatus

class EmailThreadResponse(EmailThreadBase):
    id: int
    user_id: int
    creation_date: datetime
    status: ThreadStatus

    class Config:
        from_attributes = True
