# app/schemas/email_thread_schema.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum
from uuid import UUID

class ThreadStatus(str, Enum):
    ACTIVE = "active"
    CLOSED = "closed"

class EmailThreadBase(BaseModel):
    user_id: Optional[UUID] = None
    

class EmailThreadCreate(EmailThreadBase):
    email: str
    name : str
    assistant_description: str

class EmailThreadUpdate(EmailThreadBase):
    status: ThreadStatus

class EmailThreadResponse(EmailThreadBase):
    id: int
    user_id: int
    creation_date: datetime
    status: ThreadStatus

    class Config:
        from_attributes = True
