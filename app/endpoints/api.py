from fastapi import APIRouter

from app.endpoints import oauth_endpoint, user_endpoint

routers = APIRouter()

routers.include_router(oauth_endpoint.router)
routers.include_router(user_endpoint.router)