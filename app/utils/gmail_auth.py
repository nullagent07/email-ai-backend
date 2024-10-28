from google.oauth2.credentials import Credentials
from google.auth.transport import requests
from google.auth.exceptions import RefreshError
from fastapi import HTTPException, status
from datetime import datetime, timedelta
import json
from app.core.config import get_app_settings
from google.auth.transport.requests import Request
import requests as http_requests

async def verify_gmail_token(access_token: str) -> dict:
    """
    Проверяет валидность Gmail access token и обновляет его при необходимости
    
    Args:
        access_token: OAuth2 access token от Google
        
    Returns:
        dict: {
            'valid': bool,
            'access_token': str, 
            'expires_in': int
        }
    """
    try:
        settings = get_app_settings()
        
        # Создаем credentials с необходимыми scope
        creds = Credentials(
            token=access_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=settings.google_client_id,
            client_secret=settings.google_client_secret,
            scopes=[
                'https://www.googleapis.com/auth/gmail.readonly',
                'https://www.googleapis.com/auth/gmail.send'
            ]
        )

        # Проверяем токен через Google API
        request = Request()
        
        try:
            creds.refresh(request)
            return {
                'valid': True,
                'access_token': creds.token,
                'expires_in': 3600  # Стандартное время жизни токена
            }
            
        except RefreshError:
            # Используем http_requests для проверки токена
            response = http_requests.get(
                f"https://www.googleapis.com/oauth2/v3/tokeninfo?access_token={access_token}"
            )
            
            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Недействительный токен доступа"
                )
                
            token_info = response.json()
            # Проверяем scope
            if 'scope' in token_info:
                required_scopes = {
                    'https://www.googleapis.com/auth/gmail.readonly',
                    'https://www.googleapis.com/auth/gmail.send'
                }
                scopes = set(token_info['scope'].split(' '))
                
                if not required_scopes.issubset(scopes):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Токен не имеет необходимых прав доступа"
                    )
                    
            return {
                'valid': True,
                'access_token': access_token,
                'expires_in': int(token_info.get('expires_in', 3600))
            }
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail=f"Ошибка при проверке токена: {str(e)}"
        )
