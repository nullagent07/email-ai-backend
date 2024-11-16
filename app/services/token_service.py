from datetime import datetime, timedelta
from jose import JWTError, jwt
from app.core.config import settings

class TokenService:
    def __init__(self):
        self.secret_key = settings.secret_key
        self.algorithm = settings.algorithm
        self.access_token_expires_minutes = settings.access_token_expire_minutes

    @classmethod
    def get_instance(cls) -> 'TokenService':
        return cls()

    def create_access_token(self, data: dict ):
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=self.access_token_expires_minutes)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str):        
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            return None







