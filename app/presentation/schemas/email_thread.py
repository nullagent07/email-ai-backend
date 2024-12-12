from typing import Optional
from pydantic import BaseModel, Field, EmailStr


class EmailThreadCreate(BaseModel):
    """Schema for creating an email thread."""
    recipient_email: EmailStr = Field(..., description="Recipient's email")
    recipient_name: Optional[str] = Field(None, description="Recipient's name")
    instructions: str = Field(..., description="Instructions for the assistant for this thread")


class EmailThreadResponse(BaseModel):
    """Schema for email thread response."""
    id: str = Field(..., description="Thread ID")
    user_email: str = Field(..., description="User's email")
    recipient_email: str = Field(..., description="Recipient's email")
    recipient_name: Optional[str] = Field(None, description="Recipient's name")
    assistant_profile_id: str = Field(..., description="Assistant profile ID")
    instructions: str = Field(..., description="Instructions for the assistant for this thread")