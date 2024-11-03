# app/schemas/user_schema.py
from pydantic import BaseModel, EmailStr
from uuid import UUID

class UserBase(BaseModel):
    name: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserResponse(BaseModel):
    name: str
    email: str
    is_subscription_active: bool

    class Config:
        from_attributes = True
