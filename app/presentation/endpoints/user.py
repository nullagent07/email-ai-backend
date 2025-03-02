from typing import Annotated
import logging
from datetime import datetime

from fastapi import APIRouter, Request, HTTPException, Cookie, Depends
from fastapi.security import OAuth2PasswordBearer

from app.presentation.schemas.user import UserResponse
from core.dependency_injection import UserServiceDependency, OAuthServiceDependency

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/user", tags=["user"])


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    request: Request,
    oauth_service: OAuthServiceDependency,
    user_service: UserServiceDependency,
    access_token: Annotated[str | None, Cookie()] = None,
):
    """Получение информации о текущем пользователе."""
    if not access_token:
        raise HTTPException(
            status_code=401,
            detail="Не авторизован"
        )

    # Ищем учетные данные по токену
    credentials = await oauth_service.find_by_access_token(access_token)
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Недействительный токен"
        )

    # Получаем пользователя
    user = await user_service.find_user_by_id(credentials.user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail="Пользователь не найден"
        )

    return UserResponse(
        name=user.name,
        email=user.email or ""
    )
