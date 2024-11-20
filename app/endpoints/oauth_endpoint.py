# app/endpoints/oauth_endpoint.py

# services
from app.services.oauth_service import OAuthCredentialsService
from app.services.gmail_service import GmailService
from app.services.token_service import TokenService
from app.services.user_service import UserService

# core
from app.core.dependency import get_db
from app.core.config import get_app_settings
import secrets

# google
from google.oauth2 import id_token
from google.auth.transport.requests import Request as GoogleRequest

# fastapi
from fastapi import APIRouter, Depends, Response, Request, HTTPException, status
from fastapi.responses import RedirectResponse, JSONResponse

# other
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

settings = get_app_settings()

@router.get("/google/login")
async def google_login(
    request: Request,
    gmail_service: GmailService = Depends(GmailService.get_instance)
):
    """Начинает процесс OAuth авторизации через Google"""
    try:
        client_ip = request.client.host
        flow = await gmail_service.create_oauth_flow(client_ip)
        
        authorization_url, _ = flow.authorization_url(
            access_type='offline',
            prompt='consent',
            include_granted_scopes='true'
        )
        
        print(f"Authorization URL: {authorization_url}")
        return RedirectResponse(url=authorization_url)
        
    except Exception as e:
        print(f"Error in google_login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to start authentication flow. Please try again later."
        )
    finally:
        # Очищаем ресурсы flow в случае ошибки
        try:
            await gmail_service.cleanup_flow(client_ip)
        except Exception as cleanup_error:
            print(f"Error during flow cleanup: {cleanup_error}")

@router.get("/google/callback")
async def google_callback(
    request: Request,
    response: Response,
    code: str = None,
    error: str = None,
    oauth_service: OAuthCredentialsService = Depends(OAuthCredentialsService.get_instance),
    gmail_service: GmailService = Depends(GmailService.get_instance),
    user_service: UserService = Depends(UserService.get_instance),
    token_service: TokenService = Depends(TokenService.get_instance)
):
    try:
        if error:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Authorization failed: {error}"
            )

        # Получаем IP клиента
        client_ip = request.client.host

        # Получаем OAuth flow и обмениваем код на токены
        flow = await gmail_service.create_oauth_flow(client_ip)
        flow.fetch_token(
            authorization_response=str(request.url),
            code=code
        )

        credentials = flow.credentials
        
        # Получаем информацию о пользователе
        id_info = id_token.verify_oauth2_token(
            credentials.id_token, 
            GoogleRequest(),
            settings.google_client_id
        )

        # Извлекаем email и name из id_info
        email = id_info.get('email')
        name = id_info.get('name', email.split('@')[0])  # Если имя не предоставлено, используем часть email

        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email not provided by Google"
            )

        # Проверка существования пользователя
        user = await user_service.get_user_by_email(email)
        is_new_user = False

        # Регистрируем пользователя, если он не существует
        if not user:
            user = await user_service.register_user(
                name=name,
                email=email
            )
            is_new_user = True

        # Обновляем OAuth credentials
        await oauth_service.update_oauth_credentials(
            user_id=user.id,
            provider="google",
            access_token=credentials.token,
            refresh_token=credentials.refresh_token,
            expires_in=credentials.expiry,
            email=email,
            provider_data=id_info
        )

        user_data = {
            "sub": str(user.id)
        }

        # Генерируем JWT токен
        access_token = token_service.create_access_token(user_data)
        
        # Создаем redirect response
        redirect_response = RedirectResponse(
            url=f"{settings.frontend_url}/auth/callback",
            status_code=status.HTTP_302_FOUND
        )
        
        # Устанавливаем JWT в cookie
        redirect_response.set_cookie(
            key="access_token",
            value=f"Bearer {access_token}",  
            httponly=True,
            secure=False,  
            max_age=3600,                          
            # samesite="lax"
        )
        
        logger.info(f"Setting cookie: access_token={access_token[:10]}...")
        logger.info(f"Redirect URL: {settings.frontend_url}/auth/callback")
        logger.info(f"Response headers: {dict(redirect_response.headers)}")
        return redirect_response
        
    except Exception as e:
        print(f"Unexpected error in google_callback: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service temporarily unavailable. Please try again later."
        )
    finally:
        # Очищаем ресурсы flow в случае ошибки
        try:
            await gmail_service.cleanup_flow(client_ip)
        except Exception as cleanup_error:
            print(f"Error during flow cleanup: {cleanup_error}")

@router.post("/logout")
async def logout(response: Response):
    """Logout пользователя и удаление access_token"""

    try:
        # Удаляем куки с access_token с теми же параметрами, с которыми они были установлены
        response.delete_cookie(key="access_token")
        return {"detail": "Logout successful"}
    except Exception as e:
        # Логируем неожиданные ошибки
        print(f"Unexpected error in logout: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service temporarily unavailable. Please try again later."
        )