from typing import Optional, List
from pydantic import BaseModel, Field


class AssistantCreate(BaseModel):
    """Schema for creating a new assistant."""
    name: str = Field(..., description="Name of the assistant")
    instructions: str = Field(..., description="Instructions for the assistant")
    capabilities: List[str] = Field(
        ...,
        description="List of capabilities to enable for the assistant"
    )
    model: Optional[str] = Field(
        None,
        description="Optional model to use for the assistant"
    )
    description: Optional[str] = Field(
        None,
        description="Optional description of the assistant"
    )


class AssistantUpdate(BaseModel):
    """Schema for updating an existing assistant."""
    name: Optional[str] = Field(None, description="New name for the assistant")
    instructions: Optional[str] = Field(
        None,
        description="New instructions for the assistant"
    )
    capabilities: Optional[List[str]] = Field(
        None,
        description="New list of capabilities for the assistant"
    )
    model: Optional[str] = Field(
        None,
        description="New model for the assistant"
    )
    description: Optional[str] = Field(
        None,
        description="New description for the assistant"
    )


class AssistantResponse(BaseModel):
    """Schema for assistant response."""
    id: str = Field(..., description="Assistant ID")
    name: str = Field(..., description="Assistant name")
    instructions: str = Field(..., description="Assistant instructions")
    capabilities: List[str] = Field(..., description="Assistant capabilities")
    model: str = Field(..., description="Model used by the assistant")
    description: Optional[str] = Field(None, description="Assistant description")
    created_at: int = Field(..., description="Creation timestamp")
    modified_at: Optional[int] = Field(None, description="Last modification timestamp")
    profile_id: str = Field(..., description="ID of the assistant profile in our database")
    creator_user_id: str = Field(..., description="ID of the user who created the assistant")


class AssistantProfileResponse(BaseModel):
    """Schema for assistant profile response without OpenAI details."""
    profile_id: str = Field(..., description="ID of the assistant profile")
    instruction: str = Field(..., description="Instructions for the assistant")
