# app/schemas/user_schema.py
from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    name: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_subscription_active: bool

    class Config:
        from_attributes = True
