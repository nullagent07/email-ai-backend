from datetime import datetime, timedelta
from jose import jwt, JWTError
from app.core.config import settings
from datetime import datetime, timedelta
from app.core.config import get_app_settings

settings = get_app_settings()


def verify_access_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        return payload
    except JWTError as e:
        raise e 

def create_access_token(user_id: int) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": str(user_id),
        "exp": expire
    }
    encoded_jwt = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt 

# def create_access_token(user_id: int) -> str:
#     """Создает JWT токен для пользователя"""
#     to_encode = {"sub": str(user_id)}
#     expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
#     to_encode.update({"exp": expire})
    
#     encoded_jwt = jwt.encode(
#         to_encode, 
#         settings.secret_key, 
#         algorithm=settings.algorithm
#     )
#     return encoded_jwt

# def verify_token(token: str) -> dict:
#     """Проверяет JWT токен"""
#     try:
#         payload = jwt.decode(
#             token, 
#             settings.secret_key, 
#             algorithms=[settings.algorithm]
#         )
#         return payload
#     except:
#         return None 
        