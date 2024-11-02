# app/schemas/oauth_credentials_schema.py
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

class OAuthCredentialsBase(BaseModel):
    provider: str
    email: EmailStr

class OAuthCredentialsCreate(OAuthCredentialsBase):
    user_id: int
    access_token: str
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime] = None

class OAuthCredentialsResponse(OAuthCredentialsBase):
    id: int
    user_id: int
    expires_at: Optional[datetime] = None

    class Config:
        from_attributes = True
