from collections.abc import AsyncGenerator
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.presentation.endpoints.health import router as health_router
from core.exception_handler import (
    all_exception_handler,
    custom_validation_exception_handler,
    http_exception_handler,
    starlette_http_exception_handler,
)
from core.settings import get_app_settings
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.staticfiles import StaticFiles

from app.presentation.endpoints import auth, health, user
from core.logger import setup_json_logging

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """
    Создание и настройка приложения FastAPI.
    """
    settings = get_app_settings()
    
    # Инициализация приложения
    app = FastAPI(
        title=settings.title,
        version=settings.version,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json"
    )

    # Добавляем middleware для сессий до CORS middleware
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.secret_key,
        max_age=3600,
        same_site='lax',
        https_only=False,
        session_cookie='session',
        path='/',
    )

    # Настройка CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Подключение роутов
    app.include_router(health_router, prefix="/api")
    app.include_router(auth.router, prefix="/api")
    app.include_router(user.router, prefix="/api")

    app.add_exception_handler(RequestValidationError, custom_validation_exception_handler)  # type: ignore
    app.add_exception_handler(HTTPException, http_exception_handler)  # type: ignore
    app.add_exception_handler(Exception, all_exception_handler)  # type: ignore
    app.add_exception_handler(StarletteHTTPException, starlette_http_exception_handler)  # type: ignore

    return app


# Создание приложения на уровне модуля для uvicorn
app = create_app()

def main():
    """
    Точка входа в приложение.
    """
    # Настройка логирования
    setup_json_logging()
    
    logger.info("Application startup complete")

if __name__ == "__main__":
    main()
