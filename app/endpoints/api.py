from fastapi import APIRouter

from app.endpoints.assistants import email_assistant
from app.endpoints.auth import oauth

routers = APIRouter()

routers.include_router(email_assistant.router)
routers.include_router(oauth.router)