# app/utils/oauth_verification.py

import httpx
from app.core.config import get_app_settings

settings = get_app_settings()

async def verify_oauth_code(code: str):
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": settings.google_client_id,
        "client_secret": settings.google_client_secret,
        "redirect_uri": settings.google_redirect_uri,
        "grant_type": "authorization_code",
    }

    async with httpx.AsyncClient() as client:
        token_response = await client.post(token_url, data=data)
        if token_response.status_code != 200:
            return None
        token_data = token_response.json()

        # Используем access_token для получения информации о пользователе
        user_info_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        user_info_response = await client.get(user_info_url, headers=headers)
        if user_info_response.status_code != 200:
            return None
        user_info = user_info_response.json()

        # Объединяем данные токена и информацию о пользователе
        token_data.update(user_info)

        return token_data
