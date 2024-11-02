# from jose import jwt, JWTError
# from app.core.config import settings
# from datetime import datetime, timedelta

# def verify_access_token(token: str) -> dict:
#     try:
#         payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
#         return payload
#     except JWTError as e:
#         raise e 

# def create_access_token(user_id: int) -> str:
#     expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
#     payload = {
#         "sub": str(user_id),
#         "exp": expire
#     }
#     encoded_jwt = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
#     return encoded_jwt 