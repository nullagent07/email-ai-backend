# app/utils/oauth_verification.py

import httpx
from app.core.config import get_app_settings
from google.oauth2 import id_token
from google.auth import jwt
import requests
from google.auth.transport.requests import Request

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

# Обновляем функцию проверки токена вебхука
async def verify_google_webhook_token(token: str) -> bool:
    try:
        # Убираем префикс "Bearer"
        token = token.replace("Bearer ", "")
        
        # Создаем правильный объект Request
        request = Request()
        
        # Проверяем JWT токен
        decoded_token = id_token.verify_oauth2_token(
            token,
            request,
            audience=None,  # Позволяем любой audience, так как он динамический (URL ngrok)
            clock_skew_in_seconds=10  # Добавляем допуск по времени
        )
        
        # Проверяем, что токен от нашего сервисного аккаунта
        if decoded_token.get('email') != settings.google_service_account:
            print(f"Неверный email сервисного аккаунта: {decoded_token.get('email')}")
            return False
            
        # Проверяем, что токен не истек
        if 'exp' not in decoded_token:
            print("В токене отсутствует время истечения")
            return False
            
        print("Токен успешно проверен")
        print(f"Decoded token: {decoded_token}")
        return True
        
    except Exception as e:
        print(f"Ошибка при проверке токена: {str(e)}")
        return False