# app/endpoints/auth_endpoints.py

from fastapi import APIRouter, Depends, Response, Request, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.services.auth_service import AuthService
from app.schemas.oauth_credentials_schema import OAuthCredentialsCreate, OAuthCredentialsResponse
from app.schemas.user_schema import UserResponse
from app.core.dependency import get_db, get_current_user
from app.core.config import get_app_settings
from app.core.security import verify_access_token
from app.utils.oauth_verification import verify_oauth_code
from datetime import datetime
import secrets

router = APIRouter(prefix="/auth", tags=["auth"])

settings = get_app_settings()

@router.get("/google/login")
async def google_login(response: Response):
    """Генерирует URL для авторизации через Google"""
    
    # Генерируем state token для безопасности
    state_token = secrets.token_urlsafe(32)
    response.set_cookie(
        key="oauth_state",
        value=state_token,
        httponly=True,
        secure=False,  # Установите True в продакшене с HTTPS
        max_age=600,  # 10 минут
        path="/"
    )
    
    # Формируем URL для авторизации
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": " ".join(settings.google_scope),
        "access_type": "offline",  # Для получения refresh_token
        "state": state_token,
        "prompt": "consent"  # Всегда показывать окно согласия
    }
    
    # Создаем URL
    query_string = "&".join(f"{k}={v}" for k, v in params.items())
    authorization_url = f"https://accounts.google.com/o/oauth2/v2/auth?{query_string}"
    
    return {"authorization_url": authorization_url}

@router.get("/google/callback")
async def google_callback(
    request: Request,
    code: str,
    state: str,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """Обрабатывает callback от Google после авторизации и редиректит на фронтенд"""
    # Проверяем state token
    oauth_state = request.cookies.get("oauth_state")
    if not oauth_state or oauth_state != state:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid state token")
    
    # Проверяем код авторизации и получаем данные токена
    token_data = await verify_oauth_code(code, settings)
    if not token_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to verify Google token")
    
    # Инициализируем AuthService
    auth_service = AuthService(db)
    
    # Аутентифицируем или регистрируем пользователя
    access_token, is_new_user = await auth_service.authenticate_oauth_user(token_data)
    
    # Формируем URL для редиректа
    redirect_params = {
        "status": "success",
        "is_new_user": str(is_new_user).lower(),
        "code": code,
        "state": state
    }

    query_string = "&".join(f"{k}={v}" for k, v in redirect_params.items())
    redirect_url = f"{settings.frontend_url}/auth/callback?{query_string}"

    response = RedirectResponse(
        url=redirect_url,
        status_code=status.HTTP_303_SEE_OTHER
    )
    
    # Устанавливаем куки с access_token
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        secure=False,  # Установите True для HTTPS
        max_age=settings.access_token_expire_minutes * 60,
    )
    
    return response