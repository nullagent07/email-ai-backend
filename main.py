from fastapi import FastAPI
from core.settings import get_app_settings

settings = get_app_settings()

app = FastAPI(
    title=settings.project_name,
    version=settings.version,
    debug=settings.debug,
)

@app.get("/health")
async def health_check():
    return {"status": "ok", "environment": settings.debug}
