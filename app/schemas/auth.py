from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# Схема для начального запроса авторизации
class GoogleAuthRequest(BaseModel):
    code: str
    state: Optional[str] = None
    
# Существующие схемы
class OAuthUserCreate(BaseModel):
    email: str
    name: str
    is_subscription_active: bool = False

class OAuthCredentialsCreate(BaseModel):
    provider: str
    email: str
    access_token: str
    refresh_token: str | None
    expires_at: datetime 