from typing import Annotated
import logging

from fastapi import APIRouter, Request, HTTPException, Depends, status
from starlette.responses import RedirectResponse, JSONResponse

from core.dependency_injection import AuthServiceDependency, UserServiceDependency, OAuthServiceDependency, AuthOrchestratorDependency

from app.presentation.schemas.problem import ProblemDetail

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/{provider}/login")
async def login(
    request: Request,
    provider: str,
    auth_service: AuthServiceDependency,
    responses={
        200: {
            # "model": BaseResponseSchema,
            "description": "Запрос успешно отправлен.",
        },
        422: {
            "model": ProblemDetail,
            "description": "Неправильно набран номер.",
        },
        500: {
            "model": ProblemDetail,
            "description": "Внутренняя ошибка сервера.",            
            },
    },
):
    """Инициация процесса аутентификации через провайдера."""
    try:
        logger.info(f"Starting {provider} authentication")
        logger.debug(f"Session before login: {dict(request.session)}")
        
        if 'oauth_state' not in request.session:
            request.session['oauth_state'] = {}
            
        # Получаем URL авторизации через адаптер
        auth_url = await auth_service._adapter.get_authorization_url(request)

        return RedirectResponse(url=auth_url, status_code=302)
    except Exception as e:
        logger.error(f"Login error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при инициации аутентификации: {str(e)}"
        )


@router.get("/{provider}/callback", response_model=None)
async def callback(
    request: Request,
    provider: str,
    auth_orchestrator: AuthOrchestratorDependency,
    responses={
        200: {
            "description": "Успешная аутентификация.",
        },
        422: {
            "model": ProblemDetail,
            "description": "Неправильные параметры запроса.",
        },
        500: {
            "model": ProblemDetail,
            "description": "Внутренняя ошибка сервера.",
        },
    },
):
    """Обработка callback от провайдера OAuth."""
    try:
        token = await auth_orchestrator.handle_oauth_callback(request)
        
        # Создаем response с редиректом на фронтенд
        response = RedirectResponse(
            url="http://localhost:3000/dashboard",
            status_code=status.HTTP_302_FOUND
            )
        
        # Устанавливаем токен в httpOnly secure куки
        response.set_cookie(
            key="access_token",
            value=token["access_token"],
            httponly=True,
            secure=True,
            samesite='lax',
            max_age=3600  # время жизни токена в секундах
        )
        
        if "refresh_token" in token:
            response.set_cookie(
                key="refresh_token",
                value=token["refresh_token"],
                httponly=True,
                secure=True,
                samesite='lax',
                max_age=7*24*3600  # refresh token живет дольше
            )
            
        return response
        
    except Exception as e:
        logger.error(f"Callback error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при обработке callback: {str(e)}"
        )


@router.post("/{provider}/refresh")
async def refresh_token(
    request: Request,
    provider: str,
    refresh_token: str,
    auth_service: AuthServiceDependency
):
    """Обновление токена доступа."""
    try:
        logger.info(f"Refreshing {provider} token")
        logger.debug(f"Session in refresh: {dict(request.session)}")
        logger.debug(f"Refresh token: {refresh_token}")
        
        token_info = await auth_service.refresh_token(refresh_token)
        return {
            "message": "Токен успешно обновлен",
            "token_info": token_info
        }
    except Exception as e:
        logger.error(f"Refresh error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при обновлении токена: {str(e)}"
        )


@router.post("/{provider}/revoke")
async def revoke_token(
    request: Request,
    provider: str,
    token: str,
    auth_service: AuthServiceDependency,
    responses={
        200: {
            # "model": BaseResponseSchema,
            "description": "Запрос успешно отправлен.",
        },
        422: {
            "model": ProblemDetail,
            "description": "Неправильно набран номер.",
        },
        500: {
            "description": "Внутренняя ошибка сервера.", 
            "model": ProblemDetail
            },
    },
):
    """Отзыв токена доступа."""
    try:
        logger.info(f"Revoking {provider} token")
        logger.debug(f"Session in revoke: {dict(request.session)}")
        logger.debug(f"Token to revoke: {token}")
        
        await auth_service.revoke_token(token)
        return {"message": "Токен успешно отозван"}
    except Exception as e:
        logger.error(f"Revoke error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при отзыве токена: {str(e)}"
        )