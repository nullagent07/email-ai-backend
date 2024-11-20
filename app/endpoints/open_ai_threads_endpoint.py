from fastapi import APIRouter, Depends, Cookie, HTTPException
from typing import List
from app.services.token_service import TokenService
from app.services.open_ai_thread_service import OpenAiThreadService
from app.models.open_ai_thread import OpenAiThread, ThreadStatus
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependency import get_db
from app.schemas.open_ai_thread_schema import ThreadResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/open_ai", tags=["open_ai"])

@router.get("/threads", response_model=List[ThreadResponse])
async def get_user_threads(
    access_token: str = Cookie(None),
    db: AsyncSession = Depends(get_db),
    token_service: TokenService = Depends(TokenService.get_instance)
):
    if not access_token:
        raise HTTPException(status_code=401, detail="Access token is required")

    # Verify and decode the access token
    payload = token_service.verify_token(access_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User ID not found in token")

    # Get user threads
    thread_service = OpenAiThreadService.get_instance(db)
    threads = await thread_service.get_user_threads(user_id)
    
    return threads