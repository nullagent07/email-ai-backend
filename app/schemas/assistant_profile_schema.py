from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

class AssistantProfileBase(BaseModel):
    # name: str
    description: str

class AssistantProfileCreate(AssistantProfileBase):
    pass

class AssistantProfileUpdate(AssistantProfileBase):
    name: Optional[str] = None
    description: Optional[str] = None

class AssistantProfileResponse(AssistantProfileBase):
    id: str
    created_at: datetime
    user_id: UUID

    class Config:
        from_attributes = True 