from fastapi import APIRouter

from app.endpoints import oauth, user

routers = APIRouter()

routers.include_router(oauth.router)
routers.include_router(user.router)