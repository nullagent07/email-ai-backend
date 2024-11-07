from fastapi import APIRouter

from app.endpoints import oauth_endpoint, user_endpoint, email_endpoints

routers = APIRouter()

routers.include_router(oauth_endpoint.router)
routers.include_router(user_endpoint.router)
routers.include_router(email_endpoints.router)