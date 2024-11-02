from fastapi import APIRouter, Depends, Response, Request, HTTPException, status
from app.core.config import get_app_settings
import secrets
from google_auth_oauthlib.flow import Flow
from app.schemas.auth import GoogleAuthRequest
from app.services.auth_service import AuthService
from app.dependencies.dependency import get_auth_service
from app.utils.oauth_verification import verify_oauth_code, verify_oauth_state
from app.core.config import get_app_settings
from app.models.user import User
from app.dependencies.dependency import get_current_user
from datetime import datetime
from fastapi.responses import RedirectResponse
from app.core.security import verify_access_token


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
        secure=False,  # Для localhost используем False
        # samesite="lax",
        max_age=600,  # 10 минут
        path="/"
    )
    
    # Формируем URL для авторизации
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": " ".join(settings.google_scope),
        # "scope": settings.google_scope[2],
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
    auth_service: AuthService = Depends(get_auth_service)
):
    """Обрабатывает callback от Google после авторизации и редиректит на фронтенд"""
    await verify_oauth_state(state, request.cookies.get("oauth_state"))
    
    token_data = await verify_oauth_code(code)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to verify Google token"
        )
    
    access_token, is_new_user = await auth_service.authenticate_oauth_user(token_data)
    
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
    
    # Устанавливаем куки
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        secure=False,  # True для HTTPS
        # samesite="none",
        max_age=settings.access_token_expire_minutes * 60,
        # domain=settings.cookie_domain,  # Домен для кук
    )

    # Формируем URL для редиректа с параметрами
    
    return response

@router.post("/set-password")
async def set_password(
    password: str,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Добавляет пароль к аккаунту OAuth"""
    success = await auth_service.set_password(current_user.id, password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to set password"
        )
    return {"status": "success", "message": "Password successfully set"}

@router.get("/check")
async def check_auth(
    request: Request,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Проверяет валидность пользователя по access_token из куки"""

    # Извлекаем access_token из куки
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token is missing"
        )

    # Удаляем "Bearer " если он есть
    if access_token.startswith("Bearer "):
        access_token = access_token.split(" ")[1]

    # Проверяем валидность токена
    payload = verify_access_token(access_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token"
        )

    # Извлекаем user_id из полезной нагрузки токена
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID not found in token"
        )

    # Получаем пользователя из базы данных
    user = await auth_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return {"status": "success", "user": {"id": user.id, "username": user.username}}
