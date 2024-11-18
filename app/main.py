import logging
from pathlib import Path

from app.core.config import Settings, get_app_settings
from app.core.exception_handler import (
    all_exception_handler,
    custom_validation_exception_handler,
    http_exception_handler,
    starlette_http_exception_handler,
)
from app.core.logging_config import setup_json_logging
from app.endpoints.api_endpoint import routers
from fastapi import FastAPI
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.logger import setup_logging
from app.core.middleware import RateLimitMiddleware, LoggingMiddleware, ErrorHandlingMiddleware
from app.core.exceptions import EmailAssistantException
from app.core.error_handlers import email_assistant_exception_handler, general_exception_handler
from fastapi.middleware.cors import CORSMiddleware


def get_application() -> FastAPI:
    """Returns the FastAPI application instance."""
    settings: Settings = get_app_settings()

    if settings.environment != "development":
        setup_json_logging()
        logger = logging.getLogger("odix-portal")
        logger.warning("Running in production mode")

    application = FastAPI(
        **settings.model_dump(),
        separate_input_output_schemas=False,
        title="Email Assistant API"
    )

    if settings.allowed_hosts:
        application.add_middleware(
            CORSMiddleware,
            # allow_origins=settings.allowed_hosts,
            allow_origins=["http://localhost:3000"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
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


logger = setup_logging()
app = get_application()