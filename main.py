from fastapi import FastAPI
from core.settings import get_app_settings

settings = get_app_settings()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    debug=settings.DEBUG,
)

@app.get("/health")
async def health_check():
    return {"status": "ok", "environment": settings.DEBUG}
