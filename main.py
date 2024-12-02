from fastapi import FastAPI
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
from starlette.exceptions import HTTPException as StarletteHTTPException

settings = get_app_settings()

app = FastAPI(
    title=settings.title,
    version=settings.version,
    debug=settings.debug,
)

# Регистрируем обработчики исключений

app.add_exception_handler(RequestValidationError, custom_validation_exception_handler)  # type: ignore
app.add_exception_handler(HTTPException, http_exception_handler)  # type: ignore
app.add_exception_handler(Exception, all_exception_handler)  # type: ignore
app.add_exception_handler(StarletteHTTPException, starlette_http_exception_handler)  # type: ignore

# Подключаем роутеры
app.include_router(health_router)
