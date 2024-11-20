from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from app.models.open_ai_thread import ThreadStatus

class ThreadResponse(BaseModel):
    id: str
    user_id: UUID
    creation_date: datetime
    description: str | None
    status: ThreadStatus
    assistant_id: str | None
    recipient_email: str
    recipient_name: str | None
    sender_email: str
    sender_name: str | None

    class Config:
        from_attributes = True