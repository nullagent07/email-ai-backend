from fastapi import FastAPI
from app.presentation.endpoints.health import router as health_router
from core.settings import get_app_settings

settings = get_app_settings()

app = FastAPI(
    title=settings.title,
    version=settings.version,
    debug=settings.debug,
)

# Подключаем роутеры
app.include_router(health_router)
