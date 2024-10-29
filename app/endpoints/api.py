from fastapi import APIRouter

from app.endpoints.assistants import email_assistant

routers = APIRouter()

routers.include_router(email_assistant.router)