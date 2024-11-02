# app/schemas/email_message_schema.py
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from enum import Enum

class MessageType(str, Enum):
    INCOMING = "incoming"
    OUTGOING = "outgoing"

class EmailMessageBase(BaseModel):
    thread_id: int
    subject: str
    content: str
    sender_email: EmailStr
    recipient_email: EmailStr

class EmailMessageCreate(EmailMessageBase):
    pass

class EmailMessageResponse(EmailMessageBase):
    id: int
    message_type: MessageType
    sent_at: datetime

    class Config:
        from_attributes = True

