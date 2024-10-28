from pydantic import BaseModel, EmailStr
from datetime import datetime
from enum import Enum

class ThreadCreate(BaseModel):
    name: str
    email: EmailStr
    first_message: str
    description_message: str
