from fastapi import APIRouter

from app.endpoints import oauth_endpoint, user_endpoint, email_endpoints, open_ai_threads_endpoint

routers = APIRouter()

routers.include_router(oauth_endpoint.router)
routers.include_router(user_endpoint.router)
routers.include_router(email_endpoints.router)
routers.include_router(open_ai_threads_endpoint.router)