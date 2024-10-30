from app.core.config import get_app_settings
import aiohttp
from typing import Optional, Dict
from fastapi import HTTPException, status

async def verify_oauth_code(code: str) -> Dict:
    """
    Верифицирует код авторизации OAuth и получает информацию о пользователе
    """
    settings = get_app_settings()
    print(f"Using redirect URI: {settings.google_redirect_uri}")
    print(f"Using client ID: {settings.google_client_id}")
    
    # Получаем access token
    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        "code": code,
        "client_id": settings.google_client_id,
        "client_secret": settings.google_client_secret,
        "redirect_uri": settings.google_redirect_uri,
        "grant_type": "authorization_code"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            # Получаем токены
            async with session.post(token_url, data=token_data) as resp:
                if resp.status != 200:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Failed to obtain access token"
                    )
                token_info = await resp.json()
            
            # Получаем информацию о пользователе
            headers = {"Authorization": f"Bearer {token_info['access_token']}"}
            async with session.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers=headers
            ) as resp:
                if resp.status != 200:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Failed to get user info"
                    )
                user_info = await resp.json()
        
        return {
            "email": user_info["email"],
            "name": user_info.get("name"),
            "access_token": token_info["access_token"],
            "refresh_token": token_info.get("refresh_token"),
            "expires_in": token_info["expires_in"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"OAuth verification failed: {str(e)}"
        ) 

async def verify_oauth_state(state: str, stored_state: str | None) -> None:
    """Проверяет валидность OAuth state токена."""
    print(f"Comparing states: request={state}, stored={stored_state}")
    if not stored_state:
        print("Warning: No stored state found in cookies")
    if stored_state and stored_state != state:
        print(f"States don't match: {stored_state} != {state}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state parameter"
        ) 