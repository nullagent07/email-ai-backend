import logging
from pathlib import Path

from app.core.config import Settings, get_app_settings
from app.core.exception_handler import (
    all_exception_handler,
    custom_validation_exception_handler,
    http_exception_handler,
    starlette_http_exception_handler,
)
from app.core.logging_config import setup_logging, logger
from app.endpoints.api_endpoint import routers
from fastapi import FastAPI
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.middleware import RateLimitMiddleware, LoggingMiddleware, ErrorHandlingMiddleware
from app.core.exceptions import EmailAssistantException
from app.core.error_handlers import email_assistant_exception_handler, general_exception_handler
from fastapi.middleware.cors import CORSMiddleware


def get_application() -> FastAPI:
    """Create FastAPI application."""
    settings: Settings = get_app_settings()

    application = FastAPI(
        title=settings.PROJECT_NAME,
        debug=settings.DEBUG,
        version=settings.VERSION,
    )

    # Setup logging
    setup_logging()

    if settings.allowed_hosts:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=["http://localhost:3000"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
            expose_headers=["Set-Cookie", "*"],  # Явно указываем Set-Cookie
            max_age=3600
        )
    application.include_router(routers, prefix=settings.api_prefix)

    application.add_middleware(RateLimitMiddleware, rate_limit_per_second=10)
    application.add_middleware(LoggingMiddleware)
    application.add_middleware(ErrorHandlingMiddleware)

    application.add_exception_handler(RequestValidationError, custom_validation_exception_handler)  # type: ignore
    application.add_exception_handler(HTTPException, http_exception_handler)  # type: ignore
    application.add_exception_handler(StarletteHTTPException, starlette_http_exception_handler)  # type: ignore
    application.add_exception_handler(Exception, all_exception_handler)  # type: ignore
    application.add_exception_handler(EmailAssistantException, email_assistant_exception_handler)
    application.add_exception_handler(Exception, general_exception_handler)

    return application


app = get_application()