# app/endpoints/auth_endpoints.py

from fastapi import APIRouter, Depends, Response, Request, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.oauth_service import OAuthService
from app.core.dependency import get_db
from app.core.config import get_app_settings
# from app.utils.oauth_verification import verify_oauth_code
import secrets
from app.services.gmail_service import GmailService
from google_auth_oauthlib.flow import Flow



router = APIRouter(prefix="/auth", tags=["auth"])

settings = get_app_settings()

@router.get("/google/login")
async def google_login(
    response: Response,
    gmail_service: GmailService = Depends(GmailService.get_instance)
):
    """Генерирует URL для авторизации через Google"""

    # Генерируем state token для безопасности
    state_token = secrets.token_urlsafe(32)

    # Устанавливаем куки с state token
    response.set_cookie(
        key="oauth_state",
        value=state_token,
        httponly=True,
        secure=False,  # Установите True для HTTPS в продакшене
        max_age=600,  # 10 минут
        path="/"
    )
    
    # Создаем OAuth flow
    flow = await gmail_service.create_oauth_flow()

    # Генерируем URL для авторизации
    authorization_url, _ = flow.authorization_url(
        access_type="offline",  # Для получения refresh_token
        state=state_token,
        prompt="consent"  # Всегда показывать окно согласия
    )

    return {"authorization_url": authorization_url}

@router.get("/google/callback")
async def google_callback(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
    code: str = None,
    state: str = None,
    error: str = None,
    oauth_service: OAuthService = Depends(OAuthService.get_instance),
    gmail_service: GmailService = Depends(GmailService.get_instance),
):
    """Обрабатывает callback от Google после авторизации и редиректит на фронтенд"""
    # Обрабатываем ошибки авторизации от Google
    if error:
        redirect_url = f"{settings.frontend_url}/auth/callback?error={error}&state={state}"
        return RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)

    # Проверка state token
    if not (oauth_state := request.cookies.get("oauth_state")) or oauth_state != state:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid state token")

    # Создаем OAuth flow
    flow = await gmail_service.create_oauth_flow()

    # Обмениваем код авторизации на токен
    flow.fetch_token(code=code)
    credentials = flow.credentials

    # Получаем данные пользователя через токен
    token_data = {
        "access_token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "expires_in": credentials.expiry,
        "id_token": credentials.id_token,
    }

    # Аутентифицируем или регистрируем пользователя
    access_token, is_new_user = await gmail_service.authenticate_oauth_user(token_data)
    
    # Формируем URL для редиректа с параметрами
    redirect_params = {
        "status": "success",
        "is_new_user": str(is_new_user).lower(),
        "state": state
    }
    query_string = "&".join(f"{k}={v}" for k, v in redirect_params.items())
    redirect_url = f"{settings.frontend_url}/auth/callback?{query_string}"
    
    # Устанавливаем куки с access_token и выполняем редирект
    response = RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        secure=False,  # Установите True для HTTPS
        max_age=settings.access_token_expire_minutes * 60,
    )
    
    return response

@router.post("/logout")
async def logout(response: Response):
    """Logout пользователя и удаление access_token"""

    try:
        # Удаляем куки с access_token
        response.delete_cookie(key="access_token")
        return {"detail": "Logout successful"}
    except Exception as e:
        print("Ошибка при удалении куки:", e)
        return {"detail": "Logout failed", "error": str(e)}