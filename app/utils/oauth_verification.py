# app/utils/oauth_verification.py

import httpx
from app.core.config import get_app_settings
from google.oauth2 import id_token
from google.auth import jwt
import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google.auth.transport import requests
from google_auth_oauthlib.flow import InstalledAppFlow

settings = get_app_settings()


# Обновляем функцию проверки токена вебхука
async def verify_google_webhook_token(request: Request) -> bool:
    try:
        # Убираем префикс "Bearer"
        token = request.cookies.get("access_token")

        if not token:
            return False

        token = token.replace("Bearer ", "")

        print(f"Token: {token}")
        
        # Создаем правильный объект Request
        # request = Request()
        
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