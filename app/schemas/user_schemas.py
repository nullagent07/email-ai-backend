from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    email: EmailStr
    name: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_subscription_active: bool

    class Config:
        from_attributes = True