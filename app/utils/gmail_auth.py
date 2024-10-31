from google.oauth2.credentials import Credentials
from google.auth.transport import requests
from google.auth.exceptions import RefreshError
from fastapi import HTTPException, status
from datetime import datetime, timedelta
import json
from app.core.config import get_app_settings
from google.auth.transport.requests import Request
import requests as http_requests
from app.services.auth_service import AuthService

async def verify_gmail_access_token(access_token: str, auth_service: AuthService) -> dict:
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
        # Получаем credentials из базы по токену
        oauth_creds = await auth_service._repository.get_oauth_credentials_by_token(access_token)
        
        if not oauth_creds:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token not found"
            )
            
        # Проверяем срок действия
        if oauth_creds.expires_at < datetime.utcnow():
            # Пробуем обновить токен
            return await auth_service.refresh_google_token(oauth_creds)
            
        return {
            'valid': True,
            'access_token': access_token,
            'expires_in': int((oauth_creds.expires_at - datetime.utcnow()).total_seconds())
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
